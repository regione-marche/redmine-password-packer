from PIL import Image, ImageDraw, ImageFont
import secrets
import string
import os
from config import FONT_PATH

def rimuovi_caratteri(stringa_originale, caratteri_da_rimuovere):
    """
    Rimuove i caratteri specificati dalla stringa.

    Args:
        stringa_originale: stringa di partenza
        caratteri_da_rimuovere: stringa, lista o set di caratteri da eliminare

    Returns:
        stringa pulita
    """
    # Crea un set per lookup O(1)
    da_rimuovere = set(caratteri_da_rimuovere)

    # Usa una list comprehension per filtrare
    return ''.join(c for c in stringa_originale if c not in da_rimuovere)



def genera_password(lunghezza=12):
    charset = string.ascii_letters + string.digits + string.punctuation
    charset = rimuovi_caratteri(charset, '0`\\')
    return ''.join(secrets.choice(charset) for _ in range(lunghezza))

def crea_immagine(password, ticket_id, img_dir):
    os.makedirs(img_dir, exist_ok=True)
    IMG_SIZE = (400, 100)
    img_path = os.path.join(img_dir, f'ticket_{ticket_id}_base.png')
    img = Image.new('1', IMG_SIZE, color=1)
    draw = ImageDraw.Draw(img)

    for size in range(80, 10, -1):
        try:
            font = ImageFont.truetype(FONT_PATH, size)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), password, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if w < IMG_SIZE[0] - 10 and h < IMG_SIZE[1] - 10:
            break

    x = (IMG_SIZE[0] - w) // 2
    y = (IMG_SIZE[1] - h) // 2
    draw.text((x, y), password, font=font, fill=0)
    img.save(img_path)
    return img_path
