# Simple verification command
echo "Testing import in container (syntax only, no env needed):"
python3 -c "
import ast
import os

# Check that all the modified files have correct Python syntax
files_to_check = [
    'backend/routes/admin_curriculum_routes.py',
    'backend/routes/admin_exercises_routes.py', 
    'backend/routes/admin_package_routes.py',
    'backend/routes/admin_template_routes.py',
    'backend/debug_schema_img.py'
]

all_good = True
for file_path in files_to_check:
    full_path = os.path.join('/Users/oussamaidamhane/Documents/le-maitre-mot/Projet/Le-Maitre-Mot-Refonte-Global-master-SAVE-20251225', file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            source = f.read()
        # This will raise SyntaxError if there are syntax issues
        ast.parse(source)
        print(f'✅ {file_path}: Syntax OK')
    except SyntaxError as e:
        print(f'❌ {file_path}: Syntax Error - {e}')
        all_good = False
    except Exception as e:
        print(f'⚠️ {file_path}: Error reading file - {e}')

if all_good:
    print('\n🎉 All files have valid Python syntax!')
else:
    print('\n❌ Some files have syntax errors!')
    exit(1)
"