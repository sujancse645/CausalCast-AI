import subprocess
import sys
import importlib.util
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_and_install_packages():
    packages = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'aeon': 'aeon',
        'sklearn': 'scikit-learn',
        'lightgbm': 'lightgbm',
        'xgboost': 'xgboost',
        'catboost': 'catboost',
        'joblib': 'joblib',
        'pyarrow': 'pyarrow'
    }
    
    for module_name, pip_name in packages.items():
        if importlib.util.find_spec(module_name) is None:
            logger.info(f"Package '{module_name}' is missing. Installing '{pip_name}'...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", pip_name], check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {pip_name}. Error: {e}")
                sys.exit(1)
        else:
            logger.info(f"Package '{module_name}' is already installed.")

def run_script(script_name):
    logger.info(f"\n{'='*50}\nRunning {script_name}...\n{'='*50}")
    try:
        subprocess.run([sys.executable, script_name], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"\nERROR: {script_name} failed with exit code {e.returncode}. Stopping pipeline.")
        sys.exit(1)

def main():
    logger.info("Checking dependencies...")
    check_and_install_packages()
    
    scripts = [
        r"training\inspect_tourism.py",
        r"training\preprocess_tourism.py",
        r"training\feature_engineering_tourism.py",
        r"training\prepare_tourism_training.py",
        r"training\train_lightgbm_tourism.py",
        r"training\train_xgboost_tourism.py",
        r"training\train_catboost_tourism.py",
        r"training\compare_tourism_models.py"
    ]
    
    for script in scripts:
        run_script(script)
        
    logger.info("\nTourism Quarterly Pipeline finished successfully!")

if __name__ == "__main__":
    main()
