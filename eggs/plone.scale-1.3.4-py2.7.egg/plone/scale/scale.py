from cStringIO import StringIO
import PIL.Image
import PIL.ImageFile

# Set a larger buffer size. This fixes problems with jpeg decoding.
# See http://mail.python.org/pipermail/image-sig/1999-August/000816.html for
# details.
PIL.ImageFile.MAXBLOCK = 1000000


def scaleImage(image, width=None, height=None, direction="down",
               quality=88, result=None):
    """Scale the given image data to another size and return the result
    as a string or optionally write in to the file-like `result` object.

    The `image` parameter can either be the raw image data (ie a `str`
    instance) or an open file.

    The `quality` parameter can be used to set the quality of the
    resulting image scales.

    The return value is a tuple with the new image, the image format and
    a size-tuple.  Optionally a file-like object can be given as the
    `result` parameter, in which the generated image scale will be stored.

    The `width`, `height`, `direction` parameters will be passed to
    :meth:`scalePILImage`, which performs the actual scaling.
    """
    if isinstance(image, str):
        image = StringIO(image)
    image = PIL.Image.open(image)

    # When we create a new image during scaling we loose the format
    # information, so remember it here.
    format = image.format
    if not format == 'PNG':
        format = 'JPEG'

    image = scalePILImage(image, width, height, direction)

    if result is None:
        result = StringIO()
        image.save(
            result,
            format,
            quality=quality,
            optimize=True,
            progressive=True)
        result = result.getvalue()
    else:
        image.save(
            result,
            format,
            quality=quality,
            optimize=True,
            progressive=True)
        result.seek(0)

    return result, format, image.size


def scalePILImage(image, width=None, height=None, direction="down"):
    """Scale a PIL image to another size.

    The generated image is a JPEG image, unless the original is a PNG
    image. This is needed to make sure alpha channel information is
    not lost, which JPEG does not support.

    Three different scaling options are supported:

    * `up` scaling scales the smallest dimension up to the required size
      and scrops the other dimension if needed.
    * `down` scaling starts by scaling the largest dimension to the required
      size and scrops the other dimension if needed.
    * `thumbnail` scales to the requested dimensions without cropping. The
      resulting image may have a different size than requested. This option
      requires both width and height to be specified. `keep` is accepted as
      an alternative spelling for this option, but its use is deprecated.

    The `image` parameter must be an instance of the `PIL.Image` class.

    The return value the scaled image in the form of another instance of
    `PIL.Image`.
    """
    if direction == "keep":
        direction = "thumbnail"

    if direction == "thumbnail" and not (width and height):
        raise ValueError(
            "Thumbnailing requires both width and height to be specified")
    elif width is None and height is None:
        raise ValueError("Either width or height need to be given")

    if image.mode == "1":
        # Convert black&white to grayscale
        image = image.convert("L")
    elif image.mode == "P":
        # Convert palette based images to 3x8bit+alpha
        image = image.convert("RGBA")
    elif image.mode == "CMYK":
        # Convert CMYK to RGB, allowing for web previews of print images
        image = image.convert("RGB")

    current_size = image.size
    # Determine scale factor needed to get the right height
    if height is None:
        scale_height = None
    else:
        scale_height = (float(height) / float(current_size[1]))
    if width is None:
        scale_width = None
    else:
        scale_width = (float(width) / float(current_size[0]))

    if scale_height == scale_width or direction == "thumbnail":
        # The original already has the right aspect ratio, so we only need
        # to scale.
        image.thumbnail((width, height), PIL.Image.ANTIALIAS)
    else:
        if direction == "down":
            if scale_height is None or (
                    scale_width is not None and scale_width > scale_height):
                # Width is the smallest dimension (relatively), so scale up
                # to the desired width
                new_width = width
                new_height = int(round(current_size[1] * scale_width))
            else:
                new_height = height
                new_width = int(round(current_size[0] * scale_height))
        else:
            if scale_height is None or (
                    scale_width is not None and scale_width < scale_height):
                # Width is the largest dimension (relatively), so scale up
                # to the desired width
                new_width = width
                new_height = int(round(current_size[1] * scale_width))
            else:
                new_height = height
                new_width = int(round(current_size[0] * scale_height))

        image.draft(image.mode, (new_width, new_height))
        image = image.resize((new_width, new_height), PIL.Image.ANTIALIAS)

        if (width is not None and new_width > width) or (
                height is not None and new_height > height):
            if width is None:
                left = 0
                right = new_width
            else:
                left = int((new_width - width) / 2.0)
                right = left + width
            if height is None:
                top = 0
                bottom = new_height
            else:
                top = int((new_height - height) / 2.0)
                bottom = top + height
            image = image.crop((left, top, right, bottom))

    return image
