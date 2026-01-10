import unittest
import shutil
import os
from app import app

class CMSTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        # setting up a test client for our Flask app
        self.client = app.test_client()
        self.data_path = os.path.join(os.path.dirname(__file__), 'data')
        # create a directory
        os.makedirs(self.data_path, exist_ok=True)

    def tearDown(self):
        # delete the entire directory
        shutil.rmtree(self.data_path, ignore_errors=True)

    def create_document(self, name, content=""):
        with open(os.path.join(self.data_path, name), 'w') as file:
            file.write(content)

    def admin_session(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['username'] = 'admin'
            return c
    
    def test_index(self):
        self.create_document("about.md")
        self.create_document("changes.txt")

        with self.client.get("/") as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "text/html; charset=utf-8")
            self.assertIn("about.md", response.get_data(as_text=True))
            self.assertIn("changes.txt", response.get_data(as_text=True))
            self.assertIn("New Document", response.get_data(as_text=True))
        

    def test_viewing_text_document(self):
        self.create_document('history.txt', "Python 0.9.0 (initial release) is released.")

        with self.client.get("/history.txt") as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("Python 0.9.0 (initial release) is released.", response.get_data(as_text=True))

    def test_document_not_found(self):
        # Verify that a redirect happend
        with self.client.get("histories.txt") as response:
            self.assertEqual(response.status_code, 302)

        with self.client.get(response.headers['Location']) as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("histories.txt does not exist", response.get_data(as_text=True))

        with self.client.get('/') as response:
            self.assertNotIn("histories.txt does not exist", response.get_data(as_text=True))

    def test_viewing_markdown_document(self):
        self.create_document('about.md', "# Python is...")

        response = self.client.get("/about.md")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
        self.assertIn("<h1>Python is...</h1>", response.get_data(as_text=True))


    # Edit documents - logged in and logged out users
    def test_editing_document_logged_in(self):
        self.admin_session()
        self.create_document('changes.txt')

        response = self.client.get("/changes.txt/edit")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
        self.assertIn("Edit content", response.get_data(as_text=True))
        self.assertIn("<textarea", response.get_data(as_text=True))
        self.assertIn('<button type="submit">', response.get_data(as_text=True))

    def test_editing_document_logged_out(self):
        self.create_document('changes.txt')

        response = self.client.get("/changes.txt/edit", follow_redirects=True)
        self.assertIn("You must be signed in", response.get_data(as_text=True))


    def test_updating_document_logged_in(self):
        self.admin_session()
        self.create_document('changes.txt')

        response = self.client.post("/changes.txt/edit", data={'content': "new content"})
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.headers['Location'])
        self.assertIn("changes.txt has been updated", follow_response.get_data(as_text=True))

        with self.client.get('/changes.txt') as content_response:
            self.assertEqual(content_response.status_code, 200)
            self.assertIn("new content", content_response.get_data(as_text=True))

    def test_updating_document_logged_out(self):
        self.create_document('changes.txt')

        response = self.client.post("/changes.txt/edit", data={'content': "new content"}, follow_redirects=True)

        self.assertIn("You must be signed in", response.get_data(as_text=True))        
    # View new - logged in and logged out users
    def test_view_new_document_form_logged_in(self):
        self.admin_session()

        response = self.client.get("/new")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Add a new document", response.get_data(as_text=True))
        self.assertIn('<button type="submit"', response.get_data(as_text=True))

    def test_view_new_document_form_logged_out(self):
        response = self.client.get("/new")
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.headers['Location'])

        self.assertIn("You must be signed in", follow_response.get_data(as_text=True))


    # Create documents - logged in and logged out users        
    def test_create_new_document_logged_in(self):
        self.admin_session()

        response = self.client.post("/create", 
                                    data={'filename': 'test123.txt'},
                                    follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("test123.txt has been created", response.get_data(as_text=True))

        response = self.client.get('/')
        self.assertIn('test123.txt', response.get_data(as_text=True))

    def test_create_new_document_logged_out(self):
        response = self.client.post("/create", 
                                    data={'filename': 'test123.txt'},
                                    follow_redirects=True)        

        self.assertIn("You must be signed in", response.get_data(as_text=True))
    
    def test_create_new_document_no_filename_logged_in(self):
        self.admin_session()
        response = self.client.post('/create', data={'filename': ''})        
        self.assertEqual(response.status_code, 422)
        self.assertIn("A name is required", response.get_data(as_text=True))


    # Delete documents - logged in and logged out users
    def test_deleting_document_logged_in(self):
        self.admin_session()
        self.create_document("test.txt")
        
        response = self.client.post('/test.txt/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("test.txt has been deleted",
                      response.get_data(as_text=True))

        response = self.client.get('/')
        self.assertNotIn("test.txt", response.get_data(as_text=True))
    
    def test_deleting_document_logged_out(self):
        self.create_document("test.txt")
        response = self.client.post('/test.txt/delete', follow_redirects=True)
        self.assertIn("You must be signed in", response.get_data(as_text=True))

    def test_signin_form(self):
        response = self.client.get('/users/signin')
        self.assertEqual(response.status_code, 200)
        self.assertIn("<input", response.get_data(as_text=True))
        self.assertIn('<button type="submit"', response.get_data(as_text=True))

    def test_signin(self):
        response = self.client.post('/users/signin',
                                    data={
                                        'username': 'admin',
                                        'password': 'secret',
                                    },
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Welcome", response.get_data(as_text=True))
        self.assertIn("Signed in as admin", response.get_data(as_text=True))

    def test_signin_with_bad_credentials(self):
        response = self.client.post('/users/signin',
                                    data={
                                        'username': 'guest',
                                        'password': 'shhhh',
                                    })
        self.assertEqual(response.status_code, 422)
        self.assertIn("Invalid credentials", response.get_data(as_text=True))

    def test_signout(self):
        self.client.post('/users/signin',
                         data={
                            'username': 'admin', 
                            'password': 'secret'
                        },
                        follow_redirects=True)
        response = self.client.post('/users/signout', follow_redirects=True)
        self.assertIn("You have been signed out",
                      response.get_data(as_text=True))
        self.assertIn("Sign In", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()