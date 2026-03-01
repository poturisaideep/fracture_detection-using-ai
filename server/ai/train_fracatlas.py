import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
import os
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Paths
FRACATLAS_DIR = '/Users/saideep/Downloads/FracAtlas'
CSV_PATH = os.path.join(FRACATLAS_DIR, 'dataset.csv')
IMAGE_DIR = os.path.join(FRACATLAS_DIR, 'images')

def load_and_preprocess_data(csv_path):
    df = pd.read_csv(csv_path)
    
    # Preprocess path: split by fractured status
    def get_full_path(row):
        subdir = 'Fractured' if row['fractured'] == 1 else 'Non_fractured'
        return os.path.join(subdir, row['image_id'])
    
    df['image_path'] = df.apply(get_full_path, axis=1)
    
    def get_severity(row):
        if row['fractured'] == 0:
            return 0 # Normal
        count = row['fracture_count']
        hardware = row['hardware']
        if count > 2 or row['multiscan'] == 1:
            return 3 # Severe
        if count == 2 or hardware == 1:
            return 2 # Moderate
        return 1 # Mild

    df['severity'] = df.apply(get_severity, axis=1)
    
    # Oragn labels
    organs = ['hand', 'leg', 'hip', 'shoulder']
    def get_organ(row):
        for o in organs:
            if row[o] == 1:
                return o
        return 'mixed'
    
    df['organ_label'] = df.apply(get_organ, axis=1)
    return df

def build_multi_head_model(input_shape=(224, 224, 3)):
    base_model = tf.keras.applications.DenseNet169(
        weights='imagenet', 
        include_top=False, 
        input_shape=input_shape
    )
    
    # Fine-tuning: Unfreeze the last 20 layers
    base_model.trainable = True
    for layer in base_model.layers[:-20]:
        layer.trainable = False
    
    shared = layers.GlobalAveragePooling2D()(base_model.output)
    shared = layers.BatchNormalization()(shared)
    shared = layers.Dense(512, activation='relu')(shared)
    shared = layers.Dropout(0.3)(shared)
    
    # Head 1: Organ (Hand, Leg, Hip, Shoulder, Mixed) - 5 classes
    organ_head = layers.Dense(256, activation='relu')(shared)
    organ_out = layers.Dense(5, activation='softmax', name='organ')(organ_head)
    
    # Head 2: Fracture (Binary)
    fracture_head = layers.Dense(128, activation='relu')(shared)
    fracture_out = layers.Dense(1, activation='sigmoid', name='fracture')(fracture_head)
    
    # Head 3: Severity (Normal, Mild, Moderate, Severe) - 4 classes
    severity_head = layers.Dense(256, activation='relu')(shared)
    severity_out = layers.Dense(4, activation='softmax', name='severity')(severity_head)
    
    model = models.Model(inputs=base_model.input, outputs=[organ_out, fracture_out, severity_out])
    
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-4),
        loss={
            'organ': 'sparse_categorical_crossentropy',
            'fracture': 'binary_crossentropy',
            'severity': 'sparse_categorical_crossentropy'
        },
        loss_weights={
            'organ': 0.5,
            'fracture': 2.0, 
            'severity': 1.0
        },
        metrics={
            'organ': 'accuracy',
            'fracture': 'accuracy',
            'severity': 'accuracy'
        }
    )
    
    return model

def get_data_generators(df, image_dir, batch_size=32, target_size=(224, 224), weights=None):
    train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        validation_split=0.2
    )
    
    val_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1./255,
        validation_split=0.2
    )
    
    organ_map = {'hand': 0, 'leg': 1, 'hip': 2, 'shoulder': 3, 'mixed': 4}
    df['organ_int'] = df['organ_label'].map(organ_map)
    
    # Custom generator wrapper to yield (x, y, sw) for multi-output
    def multi_generator(gen, weights=None):
        for batch_x, batch_y in gen:
            # batch_y is [organ_out, fracture_out, severity_out]
            if weights and len(batch_y) >= 2:
                f_labels = batch_y[1]
                sw_fracture = np.where(f_labels == 1, weights[1], weights[0])
                sw_tuple = (np.ones(len(f_labels)), sw_fracture, np.ones(len(f_labels)))
                yield batch_x, tuple(batch_y), sw_tuple
            else:
                yield batch_x, tuple(batch_y)

    train_base = train_datagen.flow_from_dataframe(
        df, directory=image_dir, x_col='image_path',
        y_col=['organ_int', 'fractured', 'severity'],
        target_size=target_size, batch_size=batch_size,
        class_mode='multi_output', subset='training'
    )
    
    val_base = val_datagen.flow_from_dataframe(
        df, directory=image_dir, x_col='image_path',
        y_col=['organ_int', 'fractured', 'severity'],
        target_size=target_size, batch_size=batch_size,
        class_mode='multi_output', subset='validation'
    )

    return multi_generator(train_base, weights), multi_generator(val_base), len(train_base), len(val_base)

if __name__ == "__main__":
    df = load_and_preprocess_data(CSV_PATH)
    print(f"Loaded {len(df)} images from FracAtlas")
    
    df['exists'] = df['image_path'].apply(lambda x: os.path.exists(os.path.join(IMAGE_DIR, x)))
    df = df[df['exists'] == True]
    print(f"Valid images: {len(df)}")
    
    # Calculate Class Weights for Fracture
    neg = len(df[df['fractured'] == 0])
    pos = len(df[df['fractured'] == 1])
    total = len(df)
    weight_for_0 = (1 / neg) * (total / 2.0)
    weight_for_1 = (1 / pos) * (total / 2.0)
    class_weights = [weight_for_0, weight_for_1]
    
    print(f"Calculated Class Weights: Non-Fractured={weight_for_0:.2f}, Fractured={weight_for_1:.2f}")

    model = build_multi_head_model()
    train_gen, val_gen, train_steps, val_steps = get_data_generators(df, IMAGE_DIR, weights=class_weights)
    
    checkpoint_path = '../models/fracture_model_multi.h5'
    
    # Enable Resuming: If the model already exists, load the weights
    if os.path.exists(checkpoint_path):
        print(f"Found existing model at {checkpoint_path}. Loading weights to resume training...")
        try:
            model.load_weights(checkpoint_path)
            print("Successfully loaded weights.")
        except Exception as e:
            print(f"Could not load weights: {e}. Starting from scratch.")

    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        checkpoint_path, monitor='val_loss', save_best_only=True, verbose=1
    )
    
    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss', patience=10, restore_best_weights=True
    )
    
    reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss', factor=0.2, patience=5, min_lr=1e-6, verbose=1
    )
    
    print("Starting optimized background training (30 epochs)...")
    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=30,
        steps_per_epoch=train_steps,
        validation_steps=val_steps,
        callbacks=[checkpoint, early_stop, reduce_lr]
    )
    
    print(f"Full training complete. Advanced model saved to {checkpoint_path}")
