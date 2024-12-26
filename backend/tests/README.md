# Backend Testing Guide

## Test User Environment
When executing the following commands, a dedicated test database will be created to ensure the production environment remains unaffected.

## Test Commands
Run the following commands in the backend directory to execute different types of tests:

```bash
cd backend
python manage.py test tests  # Run all test cases
python manage.py test tests.test_common_audio  # Run tests for the specified file
python manage.py test tests.test_common_audio.AudioTestCase  # Run tests for the specified class
python manage.py test tests.test_common_audio.AudioTestCase.test_1_tts_xunfei  # Run tests for the specified function
python manage.py test tests.test_app_record.RecordTestCase.inner_add # test msg
```

## Notes

When running tests in a new environment, a test_xx database will be generated. Ensure that vector support is added by modifying the app_dataforge/migrations/0001_xx.py file as follows:

```python
from django.db import migrations, models
from pgvector.django import VectorExtension
import pgvector.django.vector
import uuid

class Migration(migrations.Migration):

    initial = True

    dependencies = []

    # Add the following operation to enable vector support
    operations = [
        VectorExtension(),
        # Other operations...
    ]
```