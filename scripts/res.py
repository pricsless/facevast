import os
import subprocess
import shutil

# Configuration - Set how many times to enhance each file
ENHANCEMENT_ITERATIONS = 4  # Change this number to control how many times each file gets enhanced

# Paths
files_folder = "files"  # Folder containing images to enhance
output_folder = "output_folder"  # Main folder to save the output images

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Get all image/video files in the 'files' folder
media_files = [f for f in os.listdir(files_folder) if f.endswith(('.jpg', '.jpeg', '.png', '.mp4'))]

# Process each media file
for media_file in media_files:
    print(f"\nProcessing {media_file} with {ENHANCEMENT_ITERATIONS} iterations...")
    
    # Create a subfolder for this specific file
    file_name_without_ext = os.path.splitext(media_file)[0]
    file_output_folder = os.path.join(output_folder, file_name_without_ext)
    os.makedirs(file_output_folder, exist_ok=True)
    
    # Start with the original file
    current_input = os.path.join(files_folder, media_file)
    
    # Perform enhancement iterations
    for iteration in range(1, ENHANCEMENT_ITERATIONS + 1):
        print(f"  Iteration {iteration}/{ENHANCEMENT_ITERATIONS} for {media_file}")
        
        # Define output file for this iteration
        file_extension = os.path.splitext(media_file)[1]
        output_filename = f"{file_name_without_ext}_iteration_{iteration}{file_extension}"
        current_output = os.path.join(file_output_folder, output_filename)
        
        # Create unique job name for this iteration
        job_name = f"EnhanceJob_{file_name_without_ext}_iter_{iteration}"
        
        # Step 1: Create the job
        create_job_command = [
            "python", "facefusion.py", "job-create", job_name
        ]
        subprocess.run(create_job_command)

        # Step 2: Add the step for full image enhancement using frame enhancer and face enhancer
        add_step_command = [
            "python", "facefusion.py", "job-add-step", job_name,
            "-t", current_input, "-o", current_output,
            "--processors", "frame_enhancer", "face_enhancer",
            "--frame-enhancer-blend", "100",
            "--face-enhancer-blend", "100",
            "--frame-enhancer-model", "ultra_sharp_x4",
            "--output-image-quality", "100",
            "--output-video-quality", "100"
        ]
        subprocess.run(add_step_command)

        # Step 3: Submit the job
        submit_job_command = [
            "python", "facefusion.py", "job-submit", job_name
        ]
        subprocess.run(submit_job_command)

        # Step 4: Run the job
        run_job_command = [
            "python", "facefusion.py", "job-run", job_name
        ]
        subprocess.run(run_job_command)

        print(f"    Completed iteration {iteration}: {output_filename}")
        
        # For the next iteration, use the output of this iteration as input
        current_input = current_output
    
    print(f"Finished processing {media_file} - all iterations saved in '{file_output_folder}'")

# Step 5: Delete all jobs after processing all files
print("\nCleaning up jobs...")
delete_jobs_command = [
    "python", "facefusion.py", "job-delete-all"
]
subprocess.run(delete_jobs_command)

print("All jobs have been deleted.")
print(f"Processing complete! Check the '{output_folder}' folder for results.")