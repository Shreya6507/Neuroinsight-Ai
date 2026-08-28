# NeuroInsight AI

A demo brain MRI analysis application with sign-in, MRI upload, tumor detection, tumor type prediction, and downloadable report generation.

## Features

- Sign in page with session handling
- MRI image upload dashboard
- Simulated tumor detection logic
- Displays tumor presence, predicted type, and confidence
- Downloadable analysis report

## Requirements

- Python 3.10+
- pip

## Setup

1. Open a terminal in the project folder.
2. Create a virtual environment:

```powershell
python -m venv venv
.\\venv\\Scripts\\activate
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Run the application:

```powershell
python app.py
```

   Or use the provided launcher scripts:

```powershell
./run.ps1
```

```cmd
run.cmd
```

5. Open the browser at `http://127.0.0.1:5000`

## Login credentials

- Email: `doctor@example.com`
- Password: `password123`

Or use:

- Email: `test@example.com`
- Password: `test123`

## Notes

This application uses a placeholder MRI analysis model for demonstration. Replace `model/dummy_model.py` with a real medical model for production use.
