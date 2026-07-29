import uuid
from django.test import SimpleTestCase
from django.urls import reverse


class CategoryURLTests(SimpleTestCase):
    def test_edit_category_url_accepts_uuid(self):
        category_uuid = uuid.uuid4()
        url = reverse('edit_category', args=[category_uuid])

        self.assertEqual(url, f'/category/edit/{category_uuid}/')
