# AbsurdBot 🤖✨

![AbsurdBot](https://raw.githubusercontent.com/Ementhia/AbsurdBot/main/AbsurdBot.png)

**AbsurdBot** is a chaotic Twitter bot that automatically posts surreal, quirky images combined with random phrases and emoji, creating a stream of unpredictable, entertaining content twice daily.

---

## Features

- Mixes two random images (cats, memes, abstract pics) into one chaotic composition  
- Overlays random quotes and adds emoji spam for extra absurdity  
- Posts automatically every 12 hours using GitHub Actions  
- Supports safe-for-work content only (no NSFW)  
- Easily configurable with your Twitter API keys via GitHub Secrets  

---

## Getting Started

### Prerequisites

- Python 3.7 or newer  
- Twitter Developer account and API keys  
- GitHub repository to host the bot and run the scheduled workflow  

### Installation

1. Clone the repo:

   ```bash
   git clone https://github.com/yourusername/absurdbot.git
   cd absurdbot

2. Install the dependencies:

   ```bash
    pip install -r requirements.txt
   ```

3. Set up your Twitter API keys:

   Create a `.env` file in the root of the project and add your Twitter API keys:

   ```env
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_SECRET=your_access_secret
   ```

4. Run the bot:

   You can run the bot manually by executing:

   ```bash
   python main.py
   ```

   Alternatively, set up a GitHub Actions workflow to run the bot automatically every 12 hours.

## License


MIT License © Ementhia
