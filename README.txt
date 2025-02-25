 Online Code Editor

A web-based code editor supporting multiple programming languages with syntax highlighting and execution.

 Features
- Supports Python, JavaScript, and C++
- Code syntax highlighting using CodeMirror
- Run code directly from the browser
- Save and load code snippets
- Responsive UI with a coding-themed background
- Button animations for better user experience

 Installation and Setup

 1. Clone the Repository
```bash
git clone https://github.com/your-username/online-code-editor.git
cd online-code-editor
```

 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   For macOS/Linux
venv\Scripts\activate   For Windows
```

 3. Install Dependencies
```bash
pip install -r requirements.txt
```

 4. Run the Application
```bash
python app.py
```
The app will be accessible at `http://127.0.0.1:5000/`.

 File Structure
```
online-code-editor/
│── templates/
│   ├── index.html   Frontend UI
│── static/
│   ├── styles.css   Stylesheet
│   ├── coding-bg.jpg   Background image
│── app.py   Main Flask application
│── requirements.txt   Dependencies
│── README.md   Project documentation
```

 Deployment
You can deploy this Flask app using **Render**, **Railway**, or **Heroku**.

 Example Deployment on Render
```bash
git init
git add .
git commit -m "Initial commit"
heroku create online-code-editor
heroku config:set FLASK_APP=app.py
heroku config:set FLASK_ENV=production
git push heroku main
heroku open
```

 Contact
For any queries, contact **Ritesh Chakramani** at [riteshchakramani123@gmail.com](mailto:riteshchakramani123@gmail.com).

 License
© 2025 Ritesh Chakramani. All rights reserved.

