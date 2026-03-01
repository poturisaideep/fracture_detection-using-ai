import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
import os

def build_model(input_shape=(224, 224, 3), num_classes=4):
    """
    Builds a CNN based on DenseNet169 for multi-class severity classification.
    Classes: 0: Normal, 1: Low, 2: Moderate, 3: Critical
    """
    base_model = tf.keras.applications.DenseNet169(
        weights='imagenet', 
        include_top=False, 
        input_shape=input_shape
    )
    
    base_model.trainable = False
    
    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(512, activation='relu'),
        layers.Dense(num_classes, activation='softmax') # Multi-class output
    ])
    
    model.compile(
        optimizer=optimizers.Adam(learning_rate=5e-5),
        loss='categorical_crossentropy', # Changed for multi-class
        metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
    )
    
    return model

def get_data_generators(data_dir, batch_size=32, target_size=(224, 224), study_type=None):
    """
    Creates validation and training data generators for multi-class.
    """
    datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1./255,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.2,
        horizontal_flip=True,
        validation_split=0.2
    )

    search_path = data_dir
    if study_type:
        search_path = os.path.join(data_dir, study_type)

    train_generator = datagen.flow_from_directory(
        search_path,
        target_size=target_size,
        batch_size=batch_size,
        class_mode='categorical', # Changed for multi-class
        subset='training'
    )

    val_generator = datagen.flow_from_directory(
        search_path,
        target_size=target_size,
        batch_size=batch_size,
        class_mode='categorical', # Changed for multi-class
        subset='validation'
    )
    
    return train_generator, val_generator

if __name__ == "__main__":
    DATA_DIR = '/Users/saideep/Documents/xray-detector/server/ai/data' 
    SPECIALIZATION = 'HAND'
    
    subfolders = ['Normal', 'Severity_Low', 'Severity_Moderate', 'Severity_Critical']
    missing = [f for f in subfolders if not os.path.exists(os.path.join(DATA_DIR, SPECIALIZATION, f))]
    
    if not missing:
        # 4 Class Training: Normal, Low, Moderate, Critical
        model = build_model(num_classes=4)
        train_gen, val_gen = get_data_generators(DATA_DIR, study_type=SPECIALIZATION)
        
        model.fit(
            train_gen,
            validation_data=val_gen,
            epochs=20 # More epochs needed for multi-class
        )
        
        model_name = f'fracture_model_severity_{SPECIALIZATION.lower()}.h5'
        model.save(f'../models/{model_name}')
        print(f"Severity-aware model saved to server/models/{model_name}")
    else:
        print(f"Data folders missing in {os.path.join(DATA_DIR, SPECIALIZATION)}: {missing}")
        print("Please structure your data as: Normal, Severity_Low, Severity_Moderate, Severity_Critical")
        model = build_model(num_classes=4)
        model.summary()
