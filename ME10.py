
import argparse
from moviepy.editor import VideoFileClip, ImageSequenceClip
from PIL import Image, ImageChops, ImageOps
import numpy as np

threshold = 50

def invert_image(image):
    return ImageOps.invert(image)

def combine_images(base_image, new_image, threshold):
    # Calculate the difference between the two images
    diff = ImageChops.difference(base_image, new_image)

    # Convert to grayscale and apply threshold to create a mask
    diff = diff.convert("L")
    mask = diff.point(lambda p: 255 if p > threshold else 0)

    # Create a new image with bright green where the mask is white
    green_image = Image.new("RGB", base_image.size, color=(0, 255, 0))

    # Apply the mask to the green image
    green_mask = Image.new("L", base_image.size)
    green_mask.paste(mask, (0, 0))

    # Composite the green differences onto the new image using the threshold mask
    final_image = Image.composite(green_image, new_image, green_mask)
    return final_image

def process_video(video_path, interval, threshold, compare_first, compare_last, output_video):
    clip = VideoFileClip(video_path)
    duration = clip.duration
    current_time = 0.0
    first_frame = None
    last_frame = None
    frame_filenames = []

    while current_time <= duration:
        print(f"Processing frame at {current_time} seconds...")
        frame = clip.get_frame(current_time)
        image = Image.fromarray(frame)
        image_rgb = image.convert('RGB')

        if first_frame is None:
            first_frame = image_rgb

        if compare_first:
            final_image = combine_images(first_frame, image_rgb, threshold)
        else:
            final_image = combine_images(last_frame if last_frame is not None else image_rgb, image_rgb, threshold)

        filename = f"frame_at_{current_time}s.png"
        final_image.save(filename)
        frame_filenames.append(filename)

        last_frame = image_rgb
        current_time += interval

    if compare_last and not compare_first:
        final_image = combine_images(last_frame, first_frame, threshold)
        final_image.save(f"frame_at_{current_time}s.png")
        frame_filenames.append(f"frame_at_{current_time}s.png")

    if output_video:
        create_video(frame_filenames, interval)

    print("Processing complete.")

def create_video(frame_filenames, frame_duration):
    clip = ImageSequenceClip(frame_filenames, fps=1/frame_duration)
    clip = clip.set_duration(frame_duration * len(frame_filenames))
    clip.write_videofile("output_video.mp4", codec="libx264", fps=1/frame_duration)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a video and extract changes between frames.")
    parser.add_argument("video_path", type=str, help="Path to the video file.")
    parser.add_argument("-i", "--interval", type=float, default=1, help="Time interval between frames in seconds.")
    parser.add_argument("-t", "--threshold", type=float, default=50, help="Threshold value for differences")
    parser.add_argument("--compare-first", action="store_true", help="Compare each frame to the first frame.")
    parser.add_argument("--compare-last", action="store_true", help="Compare only the first and last frames.")
    parser.add_argument("--output-video", action="store_true", help="Create a video from the processed frames.")
    args = parser.parse_args()

    # If neither compare-first nor compare-last is specified, default to compare-last
    if not args.compare_first and not args.compare_last:
        args.compare_last = True

    process_video(args.video_path, args.interval, args.threshold, args.compare_first, args.compare_last, args.output_video)
