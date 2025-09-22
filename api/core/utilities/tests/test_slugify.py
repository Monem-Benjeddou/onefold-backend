from core.utilities.slugify import SlugUtil


class TestSlugUtil:
    def setup_method(self):
        self.slug_util = SlugUtil

    def test_slugify_basic(self):
        assert self.slug_util.slugify("Hello World") == "hello-world"

    def test_slugify_unicode(self):
        assert (
            self.slug_util.slugify("こんにちは世界", allow_unicode=True)
            == "こんにちは世界"
        )

    def test_slugify_unique(self):
        slug1 = self.slug_util.slugify("Unique Slug", unique=True)
        slug2 = self.slug_util.slugify("Unique Slug", unique=True)

        assert slug1 != slug2

        assert slug1.startswith("unique-slug-")
        assert slug2.startswith("unique-slug-")

    def test_slugify_special_characters(self):
        assert self.slug_util.slugify("This is a test!@#$%^&*()") == "this-is-a-test"

    def test_slugify_empty(self):
        assert self.slug_util.slugify("") == ""
