# Django Internationalization System

This module provides enhanced translation capabilities for Django applications, integrating with Google Translate for machine translation of `.po` files.

## Features

- Efficient multi-threaded translation of Django `.po` files
- Sophisticated caching system to minimize duplicate translations
- Support for Google Translate API
- Command-line management tools for easy translation workflows
- Automatic language detection from file paths
- Smart batching for optimal translation performance
- Progress tracking and detailed statistics

## Management Commands

### Translate Command

The main command for translation operations is `python manage.py translate`. It supports several operation modes:

#### List Available Languages

```bash
python manage.py translate --list-languages
```

#### Translate All PO Files

```bash
# Translate all untranslated strings for all non-English languages
python manage.py translate --all

# Translate all untranslated strings for specific languages
python manage.py translate --all --languages ar fr

# Force retranslation of all strings, including already translated ones
python manage.py translate --all --force

# Limit the number of entries to translate per file (for testing)
python manage.py translate --all --max-entries 100

# Use larger batch size for improved performance
python manage.py translate --all --batch-size 2000

# Increase the number of worker threads
python manage.py translate --all --max-workers 8

# Show detailed statistics
python manage.py translate --all --verbose
```

#### Translate a Specific PO File

```bash
# Translate a specific PO file (language determined from file path)
python manage.py translate --file locale/ar/LC_MESSAGES/django.po

# Translate a specific PO file with explicit language
python manage.py translate --file custom_file.po --languages ar

# Force retranslation of all strings in the file
python manage.py translate --file locale/ar/LC_MESSAGES/django.po --force
```

#### Translate a Single String

```bash
# Translate a string to all languages
python manage.py translate --string "Hello world"

# Translate a string to specific languages
python manage.py translate --string "Hello world" --languages ar fr es

# Translate from a non-English source language
python manage.py translate --string "Bonjour le monde" --source-language fr --languages ar en
```



## Programmatic Usage

You can use the translation system in your code by importing the `TranslationManager`:

```python
from apps.internationalization.services import TranslationManager

# Initialize the translation manager
translation_manager = TranslationManager(max_workers=5)

# Translate a single string
translated = translation_manager.translate_text(
    text="Hello world",
    dest_language="ar",
    source_language="en"
)

# Translate multiple strings in a batch
translations = translation_manager.translate_texts_batch(
    texts=["Hello", "Welcome", "Thank you"],
    dest_language="ar"
)

# Translate a PO file
result = translation_manager.translate_po_file(
    po_file_path="locale/ar/LC_MESSAGES/django.po",
    dest_language="ar",
    batch_size=100
)

# Translate all PO files for multiple languages
stats = translation_manager.translate_all_po_files(
    languages=["ar", "fr", "es"],
    batch_size=1000,
    force=False
)
```

## Configuration

The translation system uses Django settings to determine source/target languages:

```python
# In settings.py
LANGUAGES = [
    ("en", _("English")),  # Default source language
    ("ar", _("Arabic")),   # Target language
    ("fr", _("French")),   # Target language
]
```

## Best Practices

1. **Always review machine translations**: While the system produces good translations, human review is essential for accuracy and cultural appropriateness.

2. **Keep a backup of your translation files**: The system automatically creates backups before modifying `.po` files, but it's good practice to maintain version control.

3. **Use the caching system**: The translation cache significantly improves performance by avoiding redundant translations. Don't clear it unless necessary.

4. **Batch translations efficiently**: Use an appropriate batch size based on your needs. Larger batches are more efficient but use more memory.

5. **Consider rate limits**: When using Google Translate, be aware of API rate limits, especially for large projects.

6. **Tune max_workers for your environment**: The default of 5 worker threads is a good starting point, but you may need to adjust based on your machine's capabilities.

7. **Include context for translators**: Use context annotations in your code to provide hints for translators:

```python
# In your Python code
_("Submit")  # This could be ambiguous
_("Submit", "Button label for form submission")  # Much clearer
```

## Caching System

Translations are cached at:

```
api/locale/translation_cache/{language_code}.json
```

These caches improve performance and save on translation costs for repeated strings. The system automatically manages these caches.



## Troubleshooting

### "No language could be determined from the file path"

If using the `--file` option with a non-standard file path, you must specify the language with `--languages`.

### "Translation failed: Connection error"

When using Google Translate, check your internet connection.

### "Maximum number of worker threads exceeded"

Reduce the `--max-workers` value if your system has limited resources. 