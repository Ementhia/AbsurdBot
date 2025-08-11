import os
import requests
import tweepy
import random
import textwrap
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# ==== Config via env (set these in GitHub Secrets / env) ====
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# If you want NSFW mode, set NSFW_ALLOW="true" and provide NSFW_IMAGE_SOURCE (see notes)
NSFW_ALLOW = os.getenv("NSFW_ALLOW", "false").lower() == "true"
NSFW_IMAGE_SOURCE = os.getenv("NSFW_IMAGE_SOURCE") 
APIS = {
    "cat": "https://api.thecatapi.com/v1/images/search",
    "dog": "https://dog.ceo/api/breeds/image/random",
    "meme": "https://meme-api.com/gimme",
    "picsum": "https://picsum.photos/800/600",  
}

QUOTE_APIS = [
    "https://zenquotes.io/api/random",
    "https://api.kanye.rest/",
    "https://api.adviceslip.com/advice",
    "https://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=en"
]

EMOJI_POOL = [
    "🔥", "💀", "😳", "✨", "🤡", "🍆", "🍑", "🤖", "😈", "🥴",
    "🤣", "🙃", "🌶️", "🌈", "👑"
]

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)


def get_json(url):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_random_image_urls(count=2):

    urls = []

    if NSFW_ALLOW:
        if not NSFW_IMAGE_SOURCE:
            raise RuntimeError("NSFW mode enabled but NSFW_IMAGE_SOURCE is not provided.")
        if "," in NSFW_IMAGE_SOURCE:
            candidates = [u.strip() for u in NSFW_IMAGE_SOURCE.split(",") if u.strip()]
            while len(urls) < count:
                urls.append(random.choice(candidates))
        else:
            j = get_json(NSFW_IMAGE_SOURCE)
            if isinstance(j, list):
                cand = []
                for item in j:
                    if isinstance(item, dict):
                        cand.append(item.get("url") or item.get("image") or item.get("src"))
                    elif isinstance(item, str):
                        cand.append(item)
                cand = [c for c in cand if c]
                if not cand:
                    raise RuntimeError("NSFW image API returned no usable URLs.")
                while len(urls) < count:
                    urls.append(random.choice(cand))
            elif isinstance(j, dict):
                for k in ("url", "image", "src", "file"):
                    if k in j:
                        urls.append(j[k])
                        break
                if not urls:
                    raise RuntimeError("NSFW image API JSON didn't include a recognized image field.")
            else:
                urls = [NSFW_IMAGE_SOURCE] * count
    else:
        keys = list(APIS.keys())
        while len(urls) < count:
            choice_key = random.choice(keys)
            if choice_key in ("cat", "dog", "meme"):
                j = get_json(APIS[choice_key])
                if not j:
                    continue
                if choice_key == "cat":
                    try:
                        urls.append(j[0]["url"])
                    except Exception:
                        continue
                elif choice_key == "dog":
                    urls.append(j.get("message"))
                elif choice_key == "meme":
                    urls.append(j.get("url") or j.get("preview", [None])[-1])
            else:
                urls.append(APIS[choice_key])
    return urls[:count]


def get_random_quote():
    api_url = random.choice(QUOTE_APIS)
    try:
        resp = requests.get(api_url, timeout=10)
        data = resp.json()
        if "zenquotes" in api_url or "zenquotes.io" in api_url:
            return f"{data[0]['q']} — {data[0]['a']}"
        elif "kanye" in api_url:
            return f"“{data['quote']}” — Kanye West"
        elif "quotable" in api_url:
            return f"{data['content']} — {data['author']}"
        elif "adviceslip" in api_url:
            return f"Advice: {data['slip']['advice']}"
        elif "forismatic" in api_url:
            return f"{data['quoteText'].strip()} — {data.get('quoteAuthor', 'Unknown')}"
    except Exception:
        pass
    fallback = [
        "Life is short, smile while you still have teeth.",
        "I came. I saw. I made it weird."
    ]
    return random.choice(fallback)


def download_image(url):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGB")
    except Exception:
        return None


def mix_images(image_list):
    """
    Mixes 2 images into one composite. Strategies:
      - side_by_side
      - blend (resize to same size and blend with random alpha)
      - overlay smaller on bigger (with slight rotation)
    Returns a PIL Image.
    """
    imgs = [img for img in (download_image(u) for u in image_list) if img is not None]
    if not imgs:
        raise RuntimeError("Failed to download images.")

    if len(imgs) == 1:
        return imgs[0]

    a, b = imgs[0], imgs[1]

    target_h = 800
    def resize_preserve(img, h):
        w = int(img.width * (h / img.height))
        return img.resize((w, h), Image.LANCZOS)

    a = resize_preserve(a, target_h)
    b = resize_preserve(b, target_h)

    strat = random.choice(["side", "blend", "overlay"])

    if strat == "side":
        new_w = a.width + b.width
        out = Image.new("RGB", (new_w, target_h), (0,0,0))
        out.paste(a, (0, 0))
        out.paste(b, (a.width, 0))
        return out

    elif strat == "blend":
        min_w = min(a.width, b.width)
        a2 = a.resize((min_w, target_h), Image.LANCZOS)
        b2 = b.resize((min_w, target_h), Image.LANCZOS)
        alpha = random.uniform(0.35, 0.65)
        return Image.blend(a2, b2, alpha)

    else:
        base = a.copy()
        scale = random.uniform(0.35, 0.6)
        new_w = int(base.width * scale)
        new_h = int(b.height * (new_w / b.width))
        overlay = b.resize((new_w, new_h), Image.LANCZOS)
        max_x = max(0, base.width - new_w)
        max_y = max(0, base.height - new_h)
        left_x = int(max(base.width*0.25, 0))
        right_x = int(min(base.width*0.65 - new_w, max_x))
        left_y = int(max(base.height*0.25, 0))
        right_y = int(min(base.height*0.65 - new_h, max_y))
        if right_x < left_x:
            x = max_x // 2
        else:
            x = random.randint(left_x, right_x)
        if right_y < left_y:
            y = max_y // 2
        else:
            y = random.randint(left_y, right_y)
        overlay = overlay.rotate(random.uniform(-12,12), expand=True)
        base.paste(overlay, (x, y), overlay.convert("RGBA"))
        return base


def overlay_text(img: Image.Image, text: str):
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=34)
    except Exception:
        font = ImageFont.load_default()

    wrap_width = 30
    wrapped = textwrap.fill(text, wrap_width)

    margin = 20
    lines = wrapped.split("\n")
    total_h = sum(font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines) + (len(lines)-1)*6
    # rectangle
    rect_h = total_h + margin
    rect_w = img.width - margin*2
    x = margin
    y = img.height - rect_h - margin

    # translucent background
    overlay = Image.new("RGBA", img.size, (0,0,0,0))
    ov_draw = ImageDraw.Draw(overlay)
    ov_draw.rectangle([x-10, y-10, x+rect_w+10, y+rect_h+10], fill=(0,0,0,180))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(img)
    text_x = img.width//2
    cur_y = y + 10
    for line in lines:
        bbox = font.getbbox(line)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text(((img.width - w)/2, cur_y), line, font=font, fill=(255,255,255))
        cur_y += h + 6

    return img.convert("RGB")


def make_caption(quote):
    emojis = "".join(random.choice(EMOJI_POOL) for _ in range(random.randint(2,6)))
    hashtags = random.choice(["#FrankensteinBot", "#meme", "#chaos", "#cats"]) if random.random() < 0.6 else ""
    nonsense = random.choice(["I demand tea.", "This one me.", "Deploy the muffins."]) if random.random() < 0.35 else ""
    caption_parts = [emojis, quote, nonsense, hashtags]
    caption = " ".join([p for p in caption_parts if p]).strip()
    if len(caption) > 250:
        caption = caption[:247] + "..."
    return caption


def post_to_twitter(image_bytes: BytesIO, caption: str):
    image_bytes.seek(0)
    fn = "temp.jpg"
    media = api.media_upload(filename=fn, file=image_bytes)
    api.update_status(status=caption, media_ids=[media.media_id_string])


def main():
    try:
        image_urls = get_random_image_urls(count=2)
    except Exception as e:
        print("Failed to get image urls:", e)
        return

    animal_domains = ["thecatapi.com", "placekitten.com", "dog.ceo"]
    if NSFW_ALLOW:
        for u in image_urls:
            if any(dom in (u or "") for dom in animal_domains):
                print("Refusing to use animal image in NSFW mode. Aborting post.")
                return

    try:
        final_img = mix_images(image_urls)
    except Exception as e:
        print("Image mixing failed:", e)
        return

    quote = get_random_quote()
    if random.random() < 0.6:
        final_img = overlay_text(final_img, quote)

    caption = make_caption(quote if random.random() < 0.9 else " ")

    print("Generated Caption:\n", caption)

    final_img.save("output.png")
    print("Image saved as output.png")

    if all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
        try:
            import tweepy
            from io import BytesIO
            auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
            api = tweepy.API(auth, wait_on_rate_limit=True)
            image_bytes = BytesIO()
            final_img.save(image_bytes, format='JPEG')
            image_bytes.seek(0)
            fn = "temp.jpg"
            media = api.media_upload(filename=fn, file=image_bytes)
            api.update_status(status=caption, media_ids=[media.media_id_string])
            print("Posted to Twitter!")
        except Exception as e:
            print("Failed to post to Twitter:", e)
    else:
        print("Twitter API keys are not set. Skipping Twitter post.")

if __name__ == "__main__":
    main()
