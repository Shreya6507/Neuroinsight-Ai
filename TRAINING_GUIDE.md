# NeuroInsight AI - Model Training Guide

## Overview
This guide walks you through training the NeuroInsight AI model with the Kaggle Brain Tumor MRI Dataset.

## Prerequisites

### Python Version
- **Python 3.12** (Recommended - best compatibility)
- Python 3.13+ also supported
- ⚠️ Python 3.15 beta: Has compatibility issues with some packages (use Python 3.12 instead)
First, install the required ML packages:

```powershell
pip install -r requirements.txt
```

This installs:
- **TensorFlow** - Deep learning framework
- **Kaggle** - Dataset API
- **OpenCV** - Image processing
- **scikit-learn** - ML utilities

### 2. Set Up Kaggle API

#### Step 1: Create Kaggle Account
1. Go to https://www.kaggle.com
2. Sign up or log in with your account

#### Step 2: Generate API Credentials
1. Click your profile icon → "Settings"
2. Scroll down to "API" section
3. Click "Create New API Token"
4. This downloads `kaggle.json`

#### Step 3: Place API Key
On **Windows**, move the downloaded `kaggle.json` to:
```
C:\Users\{YourUsername}\.kaggle\kaggle.json
```

If the `.kaggle` folder doesn't exist, create it:
```powershell
mkdir $env:USERPROFILE\.kaggle
# Then copy kaggle.json there
```

Verify setup:
```powershell
kaggle datasets list
```

---

## Training the Model

### Quick Start
```powershell
cd c:\Users\SHREYA\OneDrive\Desktop\neuroinsight-ai
python model\train.py
```

### What the Training Script Does
1. **Downloads Dataset** - ~750MB from Kaggle (Brain Tumor MRI Dataset)
2. **Extracts Features** - Handcrafted features from MRI images using:
   - Histogram features
   - Statistical features (mean, std, variance, etc.)
   - Edge detection (Canny edges)
   - Texture features (Sobel filters)
   - Contrast features (CLAHE)
3. **Trains Ensemble Model** - Gradient Boosting classifier
4. **Evaluates** - Tests on validation set  
5. **Saves Model** - Weights saved to `model/trained_model.pkl` (scikit-learn)

### Training Output
You'll see progress like:
```
🧠 NeuroInsight AI - Model Training Pipeline
🔽 Downloading Brain Tumor MRI dataset from Kaggle...
✅ Dataset downloaded to ...
📂 Loading dataset...
✅ Loaded 3064 images
   Class distribution: {'glioma': 1321, 'meningioma': 739, 'pituitary': 715, 'notumor': 289}
🏗️  Creating CNN model...
✅ Model created with 2,234,980 parameters
🚀 Starting training...
Epoch 1/25
45/45 [==============================] - 120s 2s/step - loss: 1.1234 - accuracy: 0.6234 - val_loss: 0.8901 - val_accuracy: 0.7123
...
✅ Training complete!
📊 Test Accuracy: 92.45%
💾 Model saved to model/trained_model.h5
```

### Expected Training Time
- **All systems**: ~2-5 minutes (scikit-learn is very fast!)
- Feature extraction: ~1-2 minutes
- Model training: ~1-2 minutes

---

## After Training

### 1. Verify Model Files
Check that these files were created:
```
model/
  ├── trained_model.h5          # Trained model weights (~100MB)
  ├── model_checkpoint.h5        # Best checkpoint
  └── training_history.json      # Training metrics
```

### 2. Run the App
```powershell
.\run.ps1
```

Then visit: http://localhost:5000

### 3. Test with Your Images
1. Log in: `doctor@example.com` / `password123`
2. Upload an MRI image
3. The model will classify it as:
   - **Glioma** - Most common brain tumor
   - **Meningioma** - Tumor of brain membranes
   - **Pituitary** - Pituitary gland tumor
   - **No Tumor** - Normal scan

---

## Understanding the Model

### Model Architecture
```
Input (224x224x3 RGB image)
  ↓
Data Augmentation Layer
  ↓
4 Convolutional Blocks (Conv2D → BatchNorm → MaxPool → Dropout)
  ↓
Flatten Layer
  ↓
2 Dense Layers (512 → 256 neurons with Dropout)
  ↓
Output Layer (4 classes with Softmax)
```

### Classes
1. **Glioma** - Glial cell tumors (most aggressive)
2. **Meningioma** - Membrane tumors (usually benign)
3. **Pituitary** - Pituitary gland tumors
4. **No Tumor** - Normal/healthy tissue

### Expected Performance
- **Accuracy**: 90-95%
- **Precision**: High per class
- **Recall**: Balanced across classes

---

## Troubleshooting

### Problem: "Module not found: kaggle"
```powershell
pip install kaggle
```

### Problem: "kaggle: command not found" on Windows
Restart PowerShell after installing kaggle.

### Problem: "InvalidUserSecretsException" or API auth error
- Verify `C:\Users\{YourUsername}\.kaggle\kaggle.json` exists
- Check file permissions (should be readable)
- Regenerate token at kaggle.com if needed

### Problem: "No images found"
Dataset may not have downloaded. Try manual download:
1. Visit: https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset
2. Download to: `neuroinsight-ai/data/brain_tumor_mri/`
3. Run training again

### Problem: Out of Memory (OOM)
Reduce in `model/train.py`:
- `BATCH_SIZE` from 32 to 16
- `IMG_SIZE` from 224 to 128
- `EPOCHS` from 25 to 15

### Problem: Training is too slow
- Use GPU: Install [CUDA](https://developer.nvidia.com/cuda-downloads) + cuDNN
- Or reduce `BATCH_SIZE` to 16 or 8
- Or reduce `IMG_SIZE` to 128

---

## Model Files Explained

### trained_model.pkl
- Scikit-learn Gradient Boosting classifier (pickled format)
- ~20-50 MB in size
- Generated after successful training
- Used for inference (predictions)

### feature_scaler.pkl
- StandardScaler used to normalize features
- Ensures new predictions use same scaling as training
- Automatically applied during inference

### training_history.json
- JSON file with training metrics:
  - `accuracy`: Training accuracy per epoch
  - `val_accuracy`: Validation accuracy
  - `loss`: Training loss
  - `val_loss`: Validation loss
  - `test_accuracy`: Final test accuracy
  - `test_loss`: Final test loss

---

## Advanced Options

### Use Different Dataset Size
Edit `model/train.py`:
```python
VALIDATION_SPLIT = 0.2  # Change 0.2 to 0.15 for larger training set
BATCH_SIZE = 32         # Increase for faster training (needs more GPU memory)
EPOCHS = 25             # More epochs = potentially better accuracy
IMG_SIZE = 224          # Increase to 256 for more detail (slower)
```

### Resume Training
Copy `trained_model.h5` to a backup, then train again. The training script will create a new model from scratch.

### Evaluate on Custom Dataset
```python
from model.dummy_model import analyze_mri
result = analyze_mri("path/to/image.jpg")
print(result)
```

---

## Additional Resources

- **Kaggle Dataset**: https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset
- **TensorFlow Docs**: https://www.tensorflow.org/
- **Dataset Paper**: Brain Tumor Classification Using CNN (Masoud Nickparvar)

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Set up Kaggle API
3. ✅ Run training script
4. ✅ Wait for model to train
5. ✅ Test predictions on your MRI images
6. 🔄 (Optional) Fine-tune hyperparameters
7. 📊 (Optional) Deploy to production

---

Good luck with training! 🧠✨
