from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


# Create your tests here.
class MyOrderViewTest(TestCase):

    def test_no_logged_user_should_redirect(self):
        url = reverse("my_order")
        response = self.client.get(url)
        # breakpoint()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/users/login/?next=/orders/my-order")

    def test_ogged_user_should_redirect(self):
        url = reverse("my_order")
        user = get_user_model().objects.create(username="test")
        self.client.force_login(user)
        response = self.client.get(url)
        # breakpoint()
        self.assertEqual(response.status_code, 200)
