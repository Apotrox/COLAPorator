from PIL import Image, ImageDraw, ImageFont
import st7735
import math
import threading
import sys,os, time

import backend.tlv493d as tlv493d
from backend.database_manager import Manager

#---init---------


# Create ST7735 LCD display class
disp = st7735.ST7735(
                port=0, 
                cs=0, 
                dc=25, 
                backlight=None,
                rst=24, 
                width=128, 
                height=160, 
                rotation=90, 
                invert=False, 
                offset_left=2, 
                offset_top=1
)

tlv = tlv493d.TLV493D()
data_collector = threading.Thread(target=tlv.start_reading, name="TLV_Reader", daemon=True)


# Initialize display
disp.begin()
#start the data collection from TLV
data_collector.start()



#---variables------------------------

WIDTH = disp.width
HEIGHT = disp.height

img_center_x = WIDTH/2
img_center_y = HEIGHT/2 +8
radius = (HEIGHT/2)-10

slice_angles=[]

print("The first bootup can take a while. Please be patient...")

#---Rendering--------------------------------

line= Image.new("RGBA", (WIDTH, HEIGHT), color=(0,0,0,0))
line_draw=ImageDraw.Draw(line)
line_draw.line((img_center_x, img_center_y, img_center_x+radius/2, img_center_y+radius/2), fill=(255, 0, 0, 255), width=2)

font = ImageFont.load_default(16)

def render():
    while not tlv._stop_event.is_set(): #piggybacking off the tlv stop event
        time.sleep(0.04) #roughly 24fps
        angle= tlv.get_angle()
        arctan = tlv.get_arctan()
        img = Image.new("RGBA", (WIDTH, HEIGHT), color=(255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.circle((img_center_x, img_center_y), radius, outline=(0, 255, 0), fill=(0, 0, 0))

        
        rotated_line = line.rotate(-angle, resample=Image.BICUBIC, center=(img_center_x, img_center_y))
        img.paste(rotated_line, (0,0), rotated_line)
        
        textImage = Image.new("RGBA", (WIDTH, HEIGHT), color=(0,0,0,0))
        textDraw = ImageDraw.Draw(textImage)
        textDraw.text(xy=(0,0), text=str(f"{angle} deg"), font=font, fill=(255, 0, 0))
        textDraw.text(xy=(80,0), text=str(f"{arctan:.4f} rad"), font=font, fill=(255, 0, 0))
        
        img.paste(textImage, (0,0), textImage)
        
        disp.display(img)

#defining renderer thread
renderer = threading.Thread(target=render, name="Config_tool_renderer", daemon=True).start()


#----Config_functions----------------------------
try:

    def manual_config():
        """Loops through user inputs until the first value +-5 gets registered again"""
        confirm = ""
        while(confirm != "y"):
            print("""
            Please turn the wheel to the edge of the next slice
            """)
            input("Press enter to confirm position.")
            
            angle=tlv.get_angle()
            if(len(slice_angles)>0 and (angle+5 >= slice_angles[0] and angle-5 <= slice_angles[0])):
                break
            confirm = input("Is %i degrees correct? (Y/N): " %angle).lower()
            if(confirm=="n"):
                while(confirm !="y"):
                    input("Press enter to confirm position.")
                    angle=tlv.get_angle()
                    confirm = input("Is %i degrees correct? (Y/N): " %angle).lower()

            
            while(confirm != "n" and confirm != "y"):
                confirm = input("Invalid input, please try again. (Y/N): ")
            if(confirm =="y"):   
                print("Value added.")
                slice_angles.append(angle)
                confirm =""
        print(f"All values recorded: {slice_angles}")
        print("There are %i slices" % (len(slice_angles)))

    def auto_config():
        """Generates the slice angles according to the number of slices and the initial angle given"""
        
        num_slices = int(input("How many slices are there?: "))
        
        input("Please move the wheel to the nearest edge and press Enter.")
        
        initial_angle=tlv.get_angle()
        slice_angles.append(initial_angle)
        confirm = input("Is %i degrees correct? (Y/N): " %initial_angle).lower()
        if(confirm=="n"):
            while(confirm !="y"):
                input("Please move the wheel to the nearest edge and press Enter.")
                initial_angle=tlv.get_angle()
                confirm = input("Is %i degrees correct? (Y/N): " %initial_angle).lower()
        if (confirm =="y"):
            #if a circle is [0;2pi), then we can divide 2pi by the number of segments to get accurate points
            segment_length = int(math.degrees((math.pi*2)/num_slices))
            for i in range (1, num_slices):
                angle = initial_angle + segment_length*i
                if(angle <0): angle +=360
                if(angle > 360): angle -= 360
                slice_angles.append(angle)
        print(f"All values recorded: {slice_angles}")        

    def angles_to_database():
        db = Manager()
        db.ensure_database_availability()
        
        category_data = [
            (
                f"Category {i+1}", #placeholder title
                slice_angles[i], #begin angle
                slice_angles[(i+1) % len(slice_angles)] #end angle
            )
            for i in range(len(slice_angles))
        ]
        db.execute_many("INSERT INTO slices (title, angle_begin, angle_end,) VALUES (?, ?, ?)", category_data)
        db.commit_changes()
        


    #----Main-------------
    print("""
        This is a configuration tool to determine the angle of each slice.
        You will have the option to auto generate the angles by the number of slices and a starting angle,
        or set the angles yourself manually. You can also just check the angles if you'd like and not give an input.
        """)
    print("""
        Automatic generation= 1
        Manual generation= 2
        """)
    try:
        manual = int(input("Option (1,2): "))
    except ValueError:
        print("wrong input, please type 1 or 2")
        #TODO make it loop

    if manual == 2:
        print("""
            This tool stops once the first edge is registered again.
            """)
        manual_config()
    elif manual == 1:
        auto_config()
    else:
        print("wrong input")
    print(f"there are {len(slice_angles)} slices with a distance of {slice_angles[1]-slice_angles[0]}")        
    angles_to_database()
        
except KeyboardInterrupt:
    print("Exiting...")
    tlv.stop_reading()
    try:
        data_collector.join()
        renderer.join()
    except Exception:
        pass