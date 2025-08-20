import os
import subprocess

# Paths
main_image = "zoooz--.jpg"  # Your main image (for face swapping)
files_folder = "files"  # Folder containing video files to swap faces in
output_folder = "folder"  # Folder to save the output videos
os.makedirs(output_folder, exist_ok=True)
# Get all video files in the 'files' folder (assuming video files are .mp4, .mov, .avi, etc.)
video_files = [f for f in os.listdir(files_folder) if f.endswith(('.mp4', '.mov', '.m4v', '.avi'))]

# Loop through each video in the 'files' folder
for video_file in video_files:
    # Full path to the video file
    target_video = os.path.join(files_folder, video_file)
    output_video = os.path.join(output_folder, f"output_{video_file}")

    # Step 1: Create the job
    create_job_command = [
        "python", "facefusion.py", "job-create", f"BatchSwapJob_{video_file}"
    ]
    subprocess.run(create_job_command)

    # Step 2: Add the step for face swapping and enhancement (ensure video input and output formats are handled)
    add_step_command = [
        "python", "facefusion.py", "job-add-step", f"BatchSwapJob_{video_file}",
        "-s", main_image, "-t", target_video, "-o", output_video,
        "--processors", "face_swapper", "face_enhancer" , "--output-video-quality", "100",
    ]
    subprocess.run(add_step_command)

    # Step 3: Submit the job
    submit_job_command = [
        "python", "facefusion.py", "job-submit", f"BatchSwapJob_{video_file}"
    ]
    subprocess.run(submit_job_command)

    # Step 4: Run the job
    run_job_command = [
        "python", "facefusion.py", "job-run", f"BatchSwapJob_{video_file}"
    ]
    subprocess.run(run_job_command)

    print(f"Processed {video_file} and saved to {output_video}")

# Step 5: Delete all jobs after processing
delete_jobs_command = [
    "python", "facefusion.py", "job-delete-all"
]
subprocess.run(delete_jobs_command)

print("All jobs have been deleted.")