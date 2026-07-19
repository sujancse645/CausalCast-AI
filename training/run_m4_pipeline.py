import subprocess
import sys
import importlib.util

def check_and_install_packages():
    packages = {
        'lightgbm': 'lightgbm',
        'xgboost': 'xgboost',
        'catboost': 'catboost',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'pyarrow': 'pyarrow',
        'sklearn': 'scikit-learn',
        'joblib': 'joblib'
    }
    
    for module_name, pip_name in packages.items():
        if importlib.util.find_spec(module_name) is None:
            print(f"Package '{module_name}' is missing. Installing '{pip_name}'...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", pip_name], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to install {pip_name}. Error: {e}")
                sys.exit(1)
        else:
            print(f"Package '{module_name}' is already installed.")

def run_script(script_name):
    print(f"\n{'='*50}\nRunning {script_name}...\n{'='*50}")
    try:
        subprocess.run([sys.executable, script_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: {script_name} failed with exit code {e.returncode}. Stopping pipeline.")
        sys.exit(1)

def main():
    print("Checking dependencies...")
    check_and_install_packages()
    
    scripts = [
        r"training\prepare_m4_training_data.py",
        r"training\train_lightgbm_m4.py",
        r"training\train_xgboost_m4.py",
        r"training\train_catboost_m4.py",
        r"training\compare_m4_models.py"
    ]
    
    for script in scripts:
        run_script(script)
        
    print("\nPipeline finished successfully!")

if __name__ == "__main__":
    main()
