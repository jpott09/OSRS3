from PIL import Image
import os

def combine_images(image_paths:list[str],save_folder:str,scale:float = 1.0) -> str:
    """generates and saves an image from a list of image paths.  Returns the path to the generated image, or None if an error occurs."""
    paths:list[str] = image_paths
    images:list = []
    for path in paths:
        if os.path.isfile(path):
            try:
                with Image.open(path) as img:
                    copied_img = img.copy()
                    images.append(copied_img)
                    img.close()
            except Exception as e:
                print(f"Error loading image: {e}")
                return None
    try:
        total_width:int = 0
        total_height:int = 0
        for image in images:
            image = image.convert("RGBA")
            total_width += image.width
            total_height = max(total_height,image.height)
        new_image:Image = Image.new("RGBA", (total_width,total_height))
        image_x:int = 0
        for i in range(len(images)):
            image:Image = images[i]
            new_image.paste(image, (image_x,0))
            image_x += image.width
            image.close()
        #scale the image
        new_image = new_image.resize((int(new_image.width*scale),int(new_image.height*scale)))
        new_image_path:str = os.path.join(save_folder,"combined_image.png")
        #remove old image if it exists
        if os.path.isfile(new_image_path):
            os.remove(new_image_path)
        new_image.save(new_image_path)
        # release memory
        new_image.close()
        return new_image_path
    except Exception as e:
        print(f"Error combining images: {e}")
        return None