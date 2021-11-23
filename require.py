import subprocess
import sys
import os

from numpy import core
import bpy


if __name__ == "__main__":
    #install required packages
    if sys.platform.startswith('win32'):
        print("Installing dependencies ...")

        # path to python.exe
        python_exe = sys.executable

        # upgrade pip
        subprocess.call([python_exe, "-m", "ensurepip"])
        subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "setuptools"])
        subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "wheel"])

        # Windows specific install
        
        # Get PyTorch
        try:
            import torch
            print("Pytorch already installed")
        except ImportError:
            print("Pytorch to be installed.")
            # Check for CUDA version and support
            try:
                cuda = subprocess.call(['nvcc', '--version'], stdout=subprocess.PIPE)
                if b"V11" in cuda.stdout:
                    # CUDA version v11
                    subprocess.call([python_exe, "-m", "pip", "install", 
                    "torch==1.9.0+cu111", "torchvision==0.10.0+cu111", "torchaudio===0.9.0", "-f", "https://download.pytorch.org/whl/torch_stable.html"])
                elif b"V10" in cuda.stdout:
                    # CUDA version v10
                    subprocess.call([python_exe, "-m", "pip", "install",
                    "torch==1.9.0+cu102", "torchvision==0.10.0+cu111", "torchaudio===0.9.0", "-f", "https://download.pytorch.org/whl/torch_stable.html"])
            except:
                # No CUDA support
                subprocess.call([python_exe, "-m", "pip", "install", "torch", "torchvision", "torchaudio"])

        # Get OpenCV
        try:
            import cv2
            print("OpenCV already installed.")
        except ImportError:
            print("OpenCV to be installed. ")
            subprocess.call([python_exe, "-m", "pip", "install", "opencv-python"])
            
        # Get Matplotlib
        try:
            import matplotlib
            print('Matplotlib already installed.')
        except ImportError:
            print('Matplotlib to be installed.')
            subprocess.call([python_exe, "-m", "pip", "install", "matplotlib"])
            
        # Get Scikit-image
        try:
            import skimage
            print('Scikit-image already installed.')
        except ImportError:
            print('Scikit-image to be installed.')
            subprocess.call([python_exe, "-m", "pip", "install", "scikit-image"])  
            
        # Get Ipython
        try:
            import IPython
            print('IPython already installed.')
        except ImportError:
            print('IPython to be installed.')
            subprocess.call([python_exe, "-m", "pip", "install", "ipython"])  
        
        # Get tqdm
        try:
            import tqdm
            print('tqdm already installed.')
        except ImportError:
            print('tqdm to be installed.')
            subprocess.call([python_exe, "-m", "pip", "install", "tqdm"])  
            
        # Get Kornia
        try:
            import kornia
            print('kornia already installed.')
        except ImportError:
            print('kornia to be installed.')
            subprocess.call([python_exe, "-m", "pip", "install","--only-binary=numpy", "kornia"])  

        # Get Pupil Apriltags
        try:
            import pupil_apriltags
            print('pupil_apriltags already installed.')
        except ImportError:
            print('pupil_apriltags to be installed.')
            subprocess.call([python_exe, "-m", "pip", "install","pupil_apriltags"])  
        
        # Get yaml
        try:
            import yaml
            print('yaml already installed.')
        except ImportError:
            print('yaml to be installed.')
            subprocess.call([python_exe, "-m", "pip", "install","PyYaml"])  
            
        # Get hydra-core
        try:
            import hydra
            print('hydra core already installed')
        except ImportError:
            print('hydra-core to be installed')
            subprocess.call([python_exe, '-m', 'pip', 'install', 'hydra-core', '--upgrade'])

        # Get tensorboard
        try:
            import tensorboard
            print('tensorboard already installed')
        except ImportError:
            print('tensorboard to be installed')
            subprocess.call([python_exe, '-m', 'pip', 'install', 'tensorboard'])

    else:
        print("Currently we only support windows.")