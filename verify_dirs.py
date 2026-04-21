import subprocess
import os

# Change to the Bar directory
os.chdir(r'c:\Users\Gebruiker\Documents\KSA\Bar')

# Execute the batch file
result = subprocess.run(['create_dirs.bat'], shell=True, capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

print("\n" + "="*60)
print("VERIFICATION - Checking if all directories were created:")
print("="*60)

base_path = r'c:\Users\Gebruiker\Documents\KSA\Bar'
directories = [
    'database',
    'services',
    'hardware',
    'routes',
    'static\\css',
    'static\\js',
    'static\\images',
    'templates\\kiosk',
    'templates\\admin',
    'videos',
    'backups',
    'uploads\\persons',
    'uploads\\products',
]

all_exist = True
for dir_name in directories:
    dir_path = os.path.join(base_path, dir_name)
    if os.path.exists(dir_path):
        print(f"✓ {dir_name}")
    else:
        print(f"✗ {dir_name}")
        all_exist = False

print("="*60)
if all_exist:
    print("✓ SUCCESS: All 13 directories created!")
else:
    print("✗ FAILED: Some directories were not created")
