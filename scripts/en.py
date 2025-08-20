import os
import subprocess

# Paths
files_folder = "files"  # Folder containing images to enhance
output_folder = "output_folder"  # Folder to save the output images

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Get all image files in the 'files' folder
image_files = [f for f in os.listdir(files_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]

# Loop through each image in the 'files' folder
for image_file in image_files:
    # Full path to the image file
    target_image = os.path.join(files_folder, image_file)
    output_image = os.path.join(output_folder, f"enhanced_{image_file}")

    # Step 1: Create the job
    create_job_command = [
        "python", "facefusion.py", "job-create", f"EnhanceJob_{image_file}"
    ]
    subprocess.run(create_job_command)

    # Step 2: Add the step for face enhancement only
    add_step_command = [
        "python", "facefusion.py", "job-add-step", f"EnhanceJob_{image_file}",
        "-t", target_image, "-o", output_image,
        "--processors", "face_enhancer", "--face-enhancer-model", "gpen_bfr_2048" ,"--output-image-quality", "100",
    ]
    subprocess.run(add_step_command)

    # Step 3: Submit the job
    submit_job_command = [
        "python", "facefusion.py", "job-submit", f"EnhanceJob_{image_file}"
    ]
    subprocess.run(submit_job_command)

    # Step 4: Run the job
    run_job_command = [
        "python", "facefusion.py", "job-run", f"EnhanceJob_{image_file}"
    ]
    subprocess.run(run_job_command)

    print(f"Enhanced {image_file} and saved to {output_image}")

# Step 5: Delete all jobs after processing
delete_jobs_command = [
    "python", "facefusion.py", "job-delete-all"
]
subprocess.run(delete_jobs_command)

print("All jobs have been deleted.")