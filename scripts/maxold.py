import os
import subprocess
from tqdm import tqdm  # Install this with `pip install tqdm` for a progress bar

# Paths
files_folder = "files"  # Folder containing images to enhance and swap faces
main_target_folder = "main"  # Folder containing target faces for swapping
output_base_folder = "folder"  # Base folder to save all output images

# Ensure the output base folder exists
os.makedirs(output_base_folder, exist_ok=True)

# Get all image files in 'files' and target faces in 'main_target'
image_files = [f for f in os.listdir(files_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
target_faces = [f for f in os.listdir(main_target_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]

# Total tasks for progress tracking
total_tasks = len(image_files) * len(target_faces)
completed_tasks = 0

# Progress bar
progress_bar = tqdm(total=total_tasks, desc="Processing images", unit="task")

# Process each file in 'files' with each target in 'main_target' one by one
for image_file in image_files:
    source_image = os.path.join(files_folder, image_file)

    for target_face in target_faces:
        target_image = os.path.join(main_target_folder, target_face)
        target_output_folder = os.path.join(output_base_folder, os.path.splitext(target_face)[0])
        os.makedirs(target_output_folder, exist_ok=True)

        output_image = os.path.join(target_output_folder, f"{os.path.splitext(image_file)[0]}_{target_face}")

        # Step 1: Create the job
        create_job_command = [
            "python", "facefusion.py", "job-create", f"SingleSwapEnhanceJob_{image_file}_{target_face}"
        ]
        subprocess.run(create_job_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Step 2: Add the step for face swapping and enhancement
        add_step_command = [
            "python", "facefusion.py", "job-add-step", f"SingleSwapEnhanceJob_{image_file}_{target_face}",
            "-s", target_image, "-t", source_image, "-o", output_image,
            "--processors", "face_swapper", "face_enhancer",
        ]
        subprocess.run(add_step_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Step 3: Submit the job
        submit_job_command = [
            "python", "facefusion.py", "job-submit", f"SingleSwapEnhanceJob_{image_file}_{target_face}"
        ]
        subprocess.run(submit_job_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Step 4: Run the job
        run_job_command = [
            "python", "facefusion.py", "job-run", f"SingleSwapEnhanceJob_{image_file}_{target_face}"
        ]
        subprocess.run(run_job_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Log progress
        print(f"Completed: {image_file} -> {target_face}")
        completed_tasks += 1
        progress_bar.update(1)

        # Step 5: Delete the job after processing
        delete_job_command = [
            "python", "facefusion.py", "job-delete", f"SingleSwapEnhanceJob_{image_file}_{target_face}"
        ]
        subprocess.run(delete_job_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Delete the source image after all target faces have been processed
    os.remove(source_image)
    print(f"Deleted: {source_image}")

# Finalize progress bar
progress_bar.close()

print(f"All jobs completed: {completed_tasks}/{total_tasks}")