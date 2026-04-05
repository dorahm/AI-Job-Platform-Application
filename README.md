# AI Job Platform Application

An intelligent job search platform powered by AI-driven resume analysis, job matching, and application tracking.

## Features

- 🔐 **User Authentication** - Secure registration and login system
- 📄 **Resume Management** - Upload, analyze, and manage multiple resumes with AI feedback
- 🤖 **AI Analysis** - Get detailed resume quality scores and improvement recommendations
- 🎯 **Smart Job Matching** - AI-powered job recommendations based on your skills and preferences
- 📊 **Application Tracker** - Track all applications with status timeline and notes
- ✉️ **Email Generator** - Create professional application and follow-up emails
- 💬 **AI Assistant** - Chat with AI for resume tips, job search strategies, and career guidance
- 📱 **Responsive Design** - Beautiful modern UI built with dark theme and glassmorphism
- 🔔 **Notifications** - Configurable job alerts and application updates

## Tech Stack

- **Backend**: Flask, SQLAlchemy, SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Database**: SQLite (development), easily upgradeable to PostgreSQL

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/dorahm/AI-Job-Platform-Application.git
cd AI-Job-Platform-Application
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
cd ai_job_platform
python app.py
```

5. **Open in browser**
```
http://127.0.0.1:5000
```

## Project Structure

```
ai_job_platform/
├── app.py                 # Flask application and routes
├── templates/
│   └── index.html        # Main UI (includes CSS and JS)
└── static/
    ├── uploads/          # Resume uploads directory
    ├── css/              # Stylesheets
    └── js/               # JavaScript files
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Create new account
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user info

### Resume Management
- `GET /api/resumes` - List user's resumes
- `POST /api/resumes/upload` - Upload new resume
- `POST /api/resumes/<id>/analyze` - Analyze resume quality
- `POST /api/resumes/<id>/set-master` - Set master resume
- `DELETE /api/resumes/<id>` - Delete resume

### Job Matching
- `GET /api/jobs` - Get job listings with filters and pagination
  - Query params: `page`, `per_page`, `search`, `location`, `employment_type`, `industry`

### Applications
- `GET /api/applications` - List user applications
- `POST /api/applications` - Create new application
- `PUT /api/applications/<id>` - Update application status
- `DELETE /api/applications/<id>` - Delete application
- `GET /api/applications/stats` - Get stats by status

### Profile
- `PUT /api/profile` - Update user profile

### AI Chat
- `POST /api/chat` - Send message to AI assistant
- `GET /api/chat/history` - Get chat history
- `POST /api/chat/clear` - Clear chat history

### Email Tools
- `POST /api/email/generate` - Generate professional email

### CV Composer
- `POST /api/cv/compose` - Generate tailored CV/Resume

## Features in Detail

### Resume Analysis
Upload your resume and get instant AI feedback on:
- Grammar and spelling
- ATS compatibility
- Formatting and structure
- Keyword optimization
- Achievement quantification

### Smart Job Matching
Our algorithm considers:
- Your technical skills
- Location preferences
- Employment type preferences
- Industry preferences
- Years of experience

### Application Tracking
Track your entire job search journey:
- Application submission dates
- Current status (Applied, Screening, Interview, Offer, etc.)
- Follow-up dates and reminders
- Salary expectations
- Interview notes and feedback

### AI Assistant
Get help with:
- Resume optimization tips
- Job search strategies
- Professional email drafting
- Career guidance
- Interview preparation

## Database Schema

The application uses SQLAlchemy ORM with the following models:

- **User** - User accounts and profile information
- **Resume** - Resume uploads with quality scores
- **Application** - Job applications with status tracking
- **JobPosting** - Job listings in the database
- **ChatMessage** - Chat history with AI assistant

## Configuration

Edit `app.py` to modify:
```python
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobplatform.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
```

## Future Enhancements

- [ ] Real-time notifications with WebSockets
- [ ] Integration with LinkedIn API
- [ ] Email monitoring and auto-detection
- [ ] Advanced analytics and reporting
- [ ] Interview preparation module
- [ ] Salary negotiation guidance
- [ ] Team collaboration features
- [ ] Mobile app (React Native)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Support

For issues or questions, please open an issue on GitHub or contact dorahmohamed116@gmail.com

## Author

**Dorah Mohamed** - [GitHub Profile](https://github.com/dorahm)

---

**Happy job hunting! 🚀**
