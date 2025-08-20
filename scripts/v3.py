import os
import subprocess

# Paths
main_folder = "main"  # Folder containing main images for face swapping
files_folder = "files"  # Folder containing video files to swap faces in
output_folder = "folder"  # Folder to save the output videos
os.makedirs(output_folder, exist_ok=True)

# Get all image files in the 'main' folder (assuming image files are .jpg, .jpeg, .png)
image_files = [f for f in os.listdir(main_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
# Get all video files in the 'files' folder (assuming video files are .mp4, .mov, .avi, etc.)
video_files = [f for f in os.listdir(files_folder) if f.endswith(('.mp4', '.mov', '.m4v', '.avi'))]

# Loop through each image in the 'main' folder
for image_file in image_files:
    # Full path to the main image
    main_image = os.path.join(main_folder, image_file)
    
    # Loop through each video in the 'files' folder
    for video_file in video_files:
        # Full path to the video file
        target_video = os.path.join(files_folder, video_file)
        output_video = os.path.join(output_folder, f"output_{image_file}_{video_file}")

        # Step 1: Create the job
        create_job_command = [
            "python", "facefusion.py", "job-create", f"BatchSwapJob_{image_file}_{video_file}"
        ]
        subprocess.run(create_job_command)

        # Step 2: Add the step for face swapping and enhancement
        if image_file.startswith("ghader--"):
            add_step_command = [
                "python", "facefusion.py", "job-add-step", f"BatchSwapJob_{image_file}_{video_file}",
                "-s", main_image, "-t", target_video, "-o", output_video,
                "--processors", "face_swapper", "face_enhancer", "face_editor", "--face-editor-eye-open-ratio", "-0.15",
                "--output-video-quality", "90"
            ]
        else:
            add_step_command = [
                "python", "facefusion.py", "job-add-step", f"BatchSwapJob_{image_file}_{video_file}",
                "-s", main_image, "-t", target_video, "-o", output_video,
                "--processors", "face_swapper", "face_enhancer", "--output-video-quality", "90"
            ]
        subprocess.run(add_step_command)

        # Step 3: Submit the job
        submit_job_command = [
            "python", "facefusion.py", "job-submit", f"BatchSwapJob_{image_file}_{video_file}"
        ]
        subprocess.run(submit_job_command)

        # Step 4: Run the job
        run_job_command = [
            "python", "facefusion.py", "job-run", f"BatchSwapJob_{image_file}_{video_file}"
        ]
        subprocess.run(run_job_command)

        print(f"Processed {video_file} with {image_file} and saved to {output_video}")

# Step 5: Delete all jobs after processing
delete_jobs_command = [
    "python", "facefusion.py", "job-delete-all"
]
subprocess.run(delete_jobs_command)

print("All jobs have been deleted.")