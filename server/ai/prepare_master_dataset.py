import pandas as pd
import os

# Paths
FRACATLAS_DIR = '/Users/saideep/Downloads/FracAtlas'
MURA_DIR = '/Users/saideep/Downloads' # MURA paths in CSV start with MURA-v1.1/
OUTPUT_CSV = 'master_metadata.csv'

def prepare_fracatlas():
    print("Processing FracAtlas...")
    df = pd.read_csv(os.path.join(FRACATLAS_DIR, 'dataset.csv'))
    
    def get_full_path(row):
        subdir = 'Fractured' if row['fractured'] == 1 else 'Non_fractured'
        return os.path.join(FRACATLAS_DIR, 'images', subdir, row['image_id'])
    
    df['abs_path'] = df.apply(get_full_path, axis=1)
    df['source'] = 'fracatlas'
    
    # Map organs
    # FracAtlas: hand, leg, hip, shoulder, mixed
    def map_organ(row):
        if row['hand'] == 1: return 'hand'
        if row['shoulder'] == 1: return 'shoulder'
        if row['leg'] == 1 or row['hip'] == 1: return 'leg_hip'
        return 'mixed'
    
    df['body_part'] = df.apply(map_organ, axis=1)
    df['is_fractured'] = df['fractured']
    
    return df[['abs_path', 'body_part', 'is_fractured', 'source']]

def prepare_mura():
    print("Processing MURA...")
    # Load image paths and labeled studies
    # MURA-v1.1/train_labeled_studies.csv: [study_path, label]
    # MURA-v1.1/train_image_paths.csv: [image_path]
    
    train_paths = pd.read_csv('train_image_paths.csv', names=['image_path'])
    valid_paths = pd.read_csv('valid_image_paths.csv', names=['image_path'])
    all_paths = pd.concat([train_paths, valid_paths])
    
    train_labels = pd.read_csv('train_labeled_studies.csv', names=['study_path', 'label'])
    valid_labels = pd.read_csv('valid_labeled_studies.csv', names=['study_path', 'label'])
    all_labels = pd.concat([train_labels, valid_labels])
    
    # Map image to study and then to label
    # image_path example: MURA-v1.1/train/XR_SHOULDER/patient00001/study1_positive/image1.png
    # study_path example: MURA-v1.1/train/XR_SHOULDER/patient00001/study1_positive/
    
    def get_study_path(img_path):
        return '/'.join(img_path.split('/')[:-1]) + '/'
    
    all_paths['study_path'] = all_paths['image_path'].apply(get_study_path)
    
    # Merge
    df = pd.merge(all_paths, all_labels, on='study_path')
    
    df['abs_path'] = df['image_path'].apply(lambda x: os.path.join(MURA_DIR, x))
    df['source'] = 'mura'
    df['is_fractured'] = df['label']
    
    # Map body parts from MURA folder names
    # XR_ELBOW, XR_FINGER, XR_FOREARM, XR_HAND, XR_HUMERUS, XR_SHOULDER, XR_WRIST
    def map_mura_organ(img_path):
        if 'XR_HAND' in img_path or 'XR_FINGER' in img_path: return 'hand'
        if 'XR_SHOULDER' in img_path: return 'shoulder'
        if 'XR_WRIST' in img_path or 'XR_FOREARM' in img_path: return 'arm'
        if 'XR_ELBOW' in img_path or 'XR_HUMERUS' in img_path: return 'arm'
        return 'mixed'
    
    df['body_part'] = df['image_path'].apply(map_mura_organ)
    
    return df[['abs_path', 'body_part', 'is_fractured', 'source']]

if __name__ == "__main__":
    df_frac = prepare_fracatlas()
    df_mura = prepare_mura()
    
    master_df = pd.concat([df_frac, df_mura])
    
    print(f"Total images: {len(master_df)}")
    print("\nBody Part Distribution:")
    print(master_df['body_part'].value_counts())
    
    print("\nFracture Distribution:")
    print(master_df['is_fractured'].value_counts())
    
    # Filter only existing files (just to be safe)
    print("Verifying file existence (this may take a moment)...")
    master_df['exists'] = master_df['abs_path'].apply(os.path.exists)
    master_df = master_df[master_df['exists'] == True].drop(columns=['exists'])
    
    print(f"Final valid images: {len(master_df)}")
    master_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Master metadata saved to {OUTPUT_CSV}")
