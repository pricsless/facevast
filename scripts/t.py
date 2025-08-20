import os
import subprocess
from tkinter import Tk, Label, Button, Text, filedialog, messagebox, Frame
from tkinterdnd2 import TkinterDnD, DND_FILES
from threading import Thread
from tqdm import tqdm


# Function to update the log window
def update_logs(log_text, message):
    log_text.insert("end", f"{message}\n")
    log_text.see("end")


# Worker function to process images
def process_images(source_images, target_faces, log_text):
    try:
        if not source_images or not target_faces:
            raise ValueError("Both source images and target faces must be provided!")

        # Paths
        files_folder = "temp_files"
        main_folder = "temp_main"
        output_base_folder = "folder"

        # Create temporary folders
        os.makedirs(files_folder, exist_ok=True)
        os.makedirs(main_folder, exist_ok=True)

        # Copy dragged files to temp folders
        for file in source_images:
            os.rename(file, os.path.join(files_folder, os.path.basename(file)))

        for file in target_faces:
            os.rename(file, os.path.join(main_folder, os.path.basename(file)))

        # Get all images
        image_files = [f for f in os.listdir(files_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
        target_faces = [f for f in os.listdir(main_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]

        total_tasks = len(image_files) * len(target_faces)
        completed_tasks = 0

        # Progress bar in console
        progress_bar = tqdm(total=total_tasks, desc="Processing images", unit="task")

        for image_file in image_files:
            source_image = os.path.join(files_folder, image_file)

            for target_face in target_faces:
                target_image = os.path.join(main_folder, target_face)
                target_output_folder = os.path.join(output_base_folder, os.path.splitext(target_face)[0])
                os.makedirs(target_output_folder, exist_ok=True)

                output_image = os.path.join(target_output_folder, f"{os.path.splitext(image_file)[0]}_{target_face}")

                # Steps for processing
                commands = [
                    (["python", "facefusion.py", "job-create", f"Job_{image_file}_{target_face}"], "Creating job"),
                    (["python", "facefusion.py", "job-add-step", f"Job_{image_file}_{target_face}",
                      "-s", target_image, "-t", source_image, "-o", output_image,
                      "--processors", "face_swapper", "face_enhancer"], "Adding step"),
                    (["python", "facefusion.py", "job-submit", f"Job_{image_file}_{target_face}"], "Submitting job"),
                    (["python", "facefusion.py", "job-run", f"Job_{image_file}_{target_face}"], "Running job"),
                    (["python", "facefusion.py", "job-delete", f"Job_{image_file}_{target_face}"], "Deleting job"),
                ]

                for command, log_msg in commands:
                    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    update_logs(log_text, f"{log_msg}: {image_file} -> {target_face}")

                completed_tasks += 1
                progress_bar.update(1)

            os.remove(source_image)
            update_logs(log_text, f"Deleted source image: {source_image}")

        progress_bar.close()
        update_logs(log_text, "All jobs completed successfully!")
        messagebox.showinfo("Success", "Processing completed!")

    except Exception as e:
        update_logs(log_text, f"Error: {str(e)}")
        messagebox.showerror("Error", str(e))


# Main GUI setup with drag-and-drop functionality
def create_gui():
    def drop_files(target_list, event):
        files = root.splitlist(event.data)
        target_list.extend(files)
        update_logs(log_text, f"Added files: {', '.join([os.path.basename(f) for f in files])}")

    root = TkinterDnD.Tk()
    root.title("FaceFusion GUI")
    root.geometry("600x500")

    # Drag-and-drop areas
    Label(root, text="Source Images:").pack(pady=5)
    source_frame = Frame(root, relief="solid", bd=1, height=100, width=400)
    source_frame.pack(pady=5)
    source_frame.drop_target_register(DND_FILES)
    source_frame.dnd_bind("<<Drop>>", lambda e: drop_files(source_images, e))

    Label(root, text="Target Faces:").pack(pady=5)
    target_frame = Frame(root, relief="solid", bd=1, height=100, width=400)
    target_frame.pack(pady=5)
    target_frame.drop_target_register(DND_FILES)
    target_frame.dnd_bind("<<Drop>>", lambda e: drop_files(target_faces, e))

    Button(root, text="Start", bg="green", fg="white",
           command=lambda: Thread(target=process_images,
                                  args=(source_images, target_faces, log_text)).start()).pack(pady=10)

    Label(root, text="Logs:").pack(pady=5)
    log_text = Text(root, height=15, width=70)
    log_text.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    # Variables to store dragged files
    source_images = []
    target_faces = []

    create_gui()