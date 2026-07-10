print('Hello World!')
print('Testing Python environment...')

import sys
print(f'Python version: {sys.version}')

import pandas as pd
print(f'Pandas version: {pd.__version__}')

import torch
print(f'Torch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')

print('Test completed successfully!')