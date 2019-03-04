from io import BytesIO
from PIL import Image, ImageFont, ImageDraw


def write_on_image(image: BytesIO, line: list):
    text = ' '.join(line)
    img = Image.open(image)
    fnt = ImageFont.truetype('comic.ttf', 50)
    d = ImageDraw.Draw(img)
    w, h = d.textsize(text, font=fnt)

    def write_one_line(line, text_x, text_y):
        text = ' '.join(line)
        # creating black outline
        d.text((text_x - 1, text_y), text, font=fnt, fill='black')
        d.text((text_x + 1, text_y), text, font=fnt, fill='black')
        d.text((text_x, text_y - 1), text, font=fnt, fill='black')
        d.text((text_x, text_y + 1), text, font=fnt, fill='black')
        # end creating outline
        d.text((text_x, text_y), text, font=fnt)
    if w//img.width > 0:
        for word in line:  # checking if there's a single word larger than image width
            if d.textsize(word, font=fnt)[0] >= img.width:
                image.seek(0)
                return image
        lines = []
        single_line = ''
        remaining_text = text.split(' ')
        while remaining_text:
            word = remaining_text.pop(0)
            single_line_future = single_line+' '+word
            if not remaining_text and d.textsize(single_line_future, font=fnt)[0] < img.width:
                lines.append(single_line_future.strip())
            elif d.textsize(single_line_future, font=fnt)[0] > img.width:
                lines.append(single_line.strip())
                single_line = ''
                remaining_text.insert(0, word)
            else:
                single_line = single_line_future

        adjust_y = 0
        for line in lines:
            w, h = d.textsize(line, font=fnt)
            text_x = img.width // 2 - w / 2
            text_y = img.height * 2 // 3 - h / 2 + adjust_y
            adjust_y += 2*h/3
            write_one_line(line.split(' '), text_x, text_y)
    else:
        text_x = img.width // 2 - w / 2
        text_y = img.height * 2 // 3 - h / 2
        write_one_line(line, text_x, text_y)
    image.seek(0)
    img = img.convert('RGB')
    img.save(image, format='jpeg')
    image.seek(0)
    return image


def resize_image(image: BytesIO, basewidth):
    img = Image.open(image)
    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((basewidth, hsize), Image.ANTIALIAS)
    image.seek(0)
    img.save(image, format='jpeg')
    image.seek(0)
    return image
