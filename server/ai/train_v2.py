import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
import os
import cv2
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_CSV = os.path.join(SCRIPT_DIR, 'master_metadata.csv')
MODEL_PATH = os.path.join(SCRIPT_DIR, '../models/fracture_model_v2.h5')
ONLY_MURA = True # Set to True to train only on MURA dataset

def apply_clahe(image):
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to 
    enhance bone textures.
    """
    image = (image * 255).astype(np.uint8)
    # Convert to grayscale if it isn't
    if len(image.shape) == 3 and image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
        
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Back to RGB for DenseNet
    back_to_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
    return back_to_rgb.astype(np.float32) / 255.0

def build_advanced_model(input_shape=(512, 512, 3), num_organs=4):
    base_model = tf.keras.applications.DenseNet121(
        weights='imagenet', 
        include_top=False, 
        input_shape=input_shape
    )
    
    # Start frozen, we'll unfreeze later
    base_model.trainable = False
    
    inputs = layers.Input(shape=input_shape)
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(512, activation='relu')(x)
    x = layers.Dropout(0.4)(x)
    
    # Head 1: Organ (hand, shoulder, leg_hip, arm)
    organ_out = layers.Dense(num_organs, activation='softmax', name='organ')(x)
    
    # Head 2: Fracture (Binary)
    fracture_out = layers.Dense(1, activation='sigmoid', name='fracture')(x)
    
    model = models.Model(inputs=inputs, outputs=[organ_out, fracture_out])
    
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-3), # Higher LR for top-only training
        loss={
            'organ': 'sparse_categorical_crossentropy',
            'fracture': 'binary_crossentropy'
        },
        loss_weights={
            'organ': 0.5,
            'fracture': 2.0
        },
        metrics={
            'organ': 'accuracy',
            'fracture': 'accuracy'
        }
    )
    
    return model

def get_generators(df, batch_size=16, target_size=(512, 512)):
    datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1./255,
        preprocessing_function=apply_clahe,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        validation_split=0.1
    )
    
    # Consolidated organ map to maintain architecture consistency
    all_organs = ['hand', 'shoulder', 'arm', 'leg_hip']
    organ_map = {val: i for i, val in enumerate(all_organs)}
    print(f"Organ map: {organ_map}")
    df['organ_int'] = df['body_part'].map(organ_map)
    
    def multi_generator(gen):
        for batch_x, batch_y in gen:
            # batch_y is [organ_int, is_fractured]
            yield batch_x, (batch_y[0], batch_y[1])

    train_base = datagen.flow_from_dataframe(
        df, x_col='abs_path',
        y_col=['organ_int', 'is_fractured'],
        target_size=target_size, batch_size=batch_size,
        class_mode='multi_output', subset='training'
    )
    
    val_base = datagen.flow_from_dataframe(
        df, x_col='abs_path',
        y_col=['organ_int', 'is_fractured'],
        target_size=target_size, batch_size=batch_size,
        class_mode='multi_output', subset='validation'
    )

    return multi_generator(train_base), multi_generator(val_base), len(train_base), len(val_base), len(organ_map)

if __name__ == "__main__":
    df = pd.read_csv(MASTER_CSV)
    
    if ONLY_MURA:
        print("Filtering for MURA dataset only...")
        df = df[df['source'] == 'mura']
        
    print(f"Loaded {len(df)} images for training.")
    
    train_gen, val_gen, train_steps, val_steps, num_organs = get_generators(df)
    
    model = build_advanced_model(num_organs=num_organs)
    
    # Load weights if they exist to continue training
    if os.path.exists(MODEL_PATH):
        print(f"Found existing model at {MODEL_PATH}. Loading weights to resume training...")
        try:
            # We use by_name=True and skip_mismatch=True to allow loading 
            # as many weights as possible even if architecture changed slightly
            model.load_weights(MODEL_PATH, by_name=True, skip_mismatch=True)
            print("Successfully loaded weights.")
        except Exception as e:
            print(f"Could not load weights: {e}. Starting from scratch or top-only.")
    
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        MODEL_PATH, monitor='val_loss', save_best_only=True, verbose=1
    )
    
    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss', patience=5, restore_best_weights=True
    )

    tensorboard = tf.keras.callbacks.TensorBoard(
        log_dir=os.path.join(SCRIPT_DIR, 'logs'),
        histogram_freq=1,
        update_freq='batch'
    )

    # PHASE 1: Train top layers only
    print("PHASE 1: Training top layers (Frozen base)...")
    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=5,
        steps_per_epoch=train_steps,
        validation_steps=val_steps,
        callbacks=[checkpoint, early_stop, tensorboard]
    )
    
    # PHASE 2: Fine-tuning
    print("PHASE 2: Fine-tuning (Unfrozen top layers of base)...")
    base_model = model.layers[1]
    base_model.trainable = True
    # Freeze bottom layers
    for layer in base_model.layers[:-30]:
        layer.trainable = False
        
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-5), # Very low LR for fine-tuning
        loss={'organ': 'sparse_categorical_crossentropy', 'fracture': 'binary_crossentropy'},
        loss_weights={'organ': 0.5, 'fracture': 2.0},
        metrics=['accuracy']
    )
    
    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=15,
        steps_per_epoch=train_steps,
        validation_steps=val_steps,
        callbacks=[checkpoint, early_stop, tensorboard]
    )
    
    print(f"Training complete. Model saved to {MODEL_PATH}")
