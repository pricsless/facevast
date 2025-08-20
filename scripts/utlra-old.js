const ffmpeg = require("fluent-ffmpeg");
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

// =========================================================
// 🎛️ CONFIGURATION DASHBOARD
// =========================================================

// === 📁 FOLDER PATHS === //
const FILES_FOLDER = "./files";
const MAIN_FOLDER = "./main";
const OUTPUT_FOLDER = "./folder";
const EXTRACTED_FRAMES_FOLDER = path.join(OUTPUT_FOLDER, "extracted_frames");

// === 🖼️ VIDEO SETTINGS === //
const RESOLUTION_MODE = "1440p";
const QUALITY_PRESET = "veryslow";
const CRF_VALUE = 0;
const FPS = 60;
const SCALE_MODE = "fit";
const USE_PADDING = true;
const SCALING_ALGORITHM = "lanczos";

// =========================================================
// 🚀 MAIN PROCESSING PIPELINE
// =========================================================

async function main() {
	console.log("🎬 Starting Combined Video Processing Pipeline...\n");

	// Activate conda environment
	console.log("🐍 Activating facefusion conda environment...");
	try {
		execSync(
			"source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh && conda activate facefusion",
			{ stdio: "inherit", shell: true }
		);
		console.log("✅ Conda environment activated");
	} catch (error) {
		console.error("❌ CRITICAL: Could not activate conda environment!");
		console.error("Please run these commands manually first:");
		console.error(
			"source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh"
		);
		console.error("conda activate facefusion");
		throw new Error(
			"Conda environment activation failed - this is required for face fusion to work"
		);
	}

	// Create necessary directories
	if (!fs.existsSync(OUTPUT_FOLDER)) {
		fs.mkdirSync(OUTPUT_FOLDER, { recursive: true });
	}
	if (!fs.existsSync(EXTRACTED_FRAMES_FOLDER)) {
		fs.mkdirSync(EXTRACTED_FRAMES_FOLDER, { recursive: true });
	}

	try {
		// Step 1: Create video from images in files folder
		console.log("📹 STEP 1: Creating video from images in files folder...");
		const videoPath = await createVideoFromImages();

		// Step 2: Process each main image with face swapping
		console.log(
			"\n👤 STEP 2: Processing main images with face swapping..."
		);
		await processMainImages(videoPath);

		// Step 3: Extract frames from all output videos
		console.log("\n🖼️ STEP 3: Extracting frames from output videos...");
		await extractFramesFromVideos();

		// Step 4: Cleanup
		console.log("\n🧹 STEP 4: Cleaning up temporary files...");
		await cleanup(videoPath);

		console.log("\n✅ Pipeline completed successfully!");
		console.log(
			`📁 Final frames are available in: ${EXTRACTED_FRAMES_FOLDER}`
		);
	} catch (error) {
		console.error("❌ Pipeline failed:", error.message);
		process.exit(1);
	}
}

// =========================================================
// 📹 STEP 1: CREATE VIDEO FROM IMAGES
// =========================================================

function createVideoFromImages() {
	return new Promise((resolve, reject) => {
		console.log("📁 Reading images from files folder...");

		const imageFiles = fs
			.readdirSync(FILES_FOLDER)
			.filter((file) => /\.(jpg|jpeg|png)$/i.test(file))
			.sort();

		if (imageFiles.length === 0) {
			reject(new Error("No images found in files folder!"));
			return;
		}

		console.log(`🖼️ Found ${imageFiles.length} images`);

		// Rename images to sequential format
		console.log("🔄 Renaming images to sequential format...");
		imageFiles.forEach((file, index) => {
			const ext = path.extname(file);
			const newName = `img${String(index + 1).padStart(3, "0")}${ext}`;
			const oldPath = path.join(FILES_FOLDER, file);
			const newPath = path.join(FILES_FOLDER, newName);
			if (file !== newName) {
				fs.renameSync(oldPath, newPath);
			}
		});

		// Get target resolution
		let targetWidth, targetHeight;
		const resolutions = {
			"720p": [1280, 720],
			"1080p": [1920, 1080],
			"1440p": [1920, 1440],
			"2160p": [3840, 2160],
		};
		[targetWidth, targetHeight] = resolutions[RESOLUTION_MODE] || [
			1920, 1080,
		];

		// Build scaling filter
		let filterComplex;
		if (SCALE_MODE === "fit" && USE_PADDING) {
			filterComplex = `scale=w=${targetWidth}:h=${targetHeight}:flags=${SCALING_ALGORITHM}:force_original_aspect_ratio=decrease,pad=${targetWidth}:${targetHeight}:(ow-iw)/2:(oh-ih)/2`;
		} else if (SCALE_MODE === "fill") {
			filterComplex = `scale=${targetWidth}:${targetHeight}:flags=${SCALING_ALGORITHM}:force_original_aspect_ratio=increase,crop=${targetWidth}:${targetHeight}`;
		} else if (SCALE_MODE === "stretch") {
			filterComplex = `scale=${targetWidth}:${targetHeight}:flags=${SCALING_ALGORITHM}`;
		} else {
			filterComplex = `scale=${targetWidth}:${targetHeight}:flags=${SCALING_ALGORITHM}:force_original_aspect_ratio=decrease`;
		}

		const outputVideo = path.join(FILES_FOLDER, "source_video.mp4");
		const duration = imageFiles.length / FPS;

		console.log(
			`📊 Creating ${duration.toFixed(
				2
			)}s video at ${targetWidth}x${targetHeight}...`
		);

		const command = ffmpeg();
		command.input(path.join(FILES_FOLDER, "img%03d.jpg"));
		command.inputOptions([`-framerate ${FPS}`]);

		command
			.inputFPS(FPS)
			.outputOptions([
				"-c:v libx264",
				"-pix_fmt yuv420p",
				`-preset ${QUALITY_PRESET}`,
				`-crf ${CRF_VALUE}`,
				`-r ${FPS}`,
				"-vf",
				filterComplex,
			])
			.on("start", () => console.log("🎬 FFmpeg encoding started"))
			.on("progress", (progress) => {
				if (progress.percent) {
					process.stdout.write(
						`⏳ Progress: ${Math.floor(progress.percent)}%\r`
					);
				}
			})
			.on("end", () => {
				console.log("\n✅ Source video created successfully!");

				// Delete original images after video creation
				const renamedImages = fs
					.readdirSync(FILES_FOLDER)
					.filter((file) => /^img\d{3}\.(jpg|jpeg|png)$/i.test(file));

				renamedImages.forEach((file) => {
					fs.unlinkSync(path.join(FILES_FOLDER, file));
				});

				console.log("🗑️ Original images deleted from files folder");
				resolve(outputVideo);
			})
			.on("error", (err) => reject(err))
			.save(outputVideo);
	});
}

// =========================================================
// 👤 STEP 2: PROCESS MAIN IMAGES WITH FACE SWAPPING
// =========================================================

async function processMainImages(videoPath) {
	console.log("📁 Reading main images...");

	const mainImages = fs
		.readdirSync(MAIN_FOLDER)
		.filter((file) => /\.(jpg|jpeg|png)$/i.test(file))
		.sort();

	if (mainImages.length === 0) {
		throw new Error("No images found in main folder!");
	}

	console.log(`👤 Found ${mainImages.length} main images to process`);

	for (let i = 0; i < mainImages.length; i++) {
		const mainImage = mainImages[i];
		const mainImagePath = path.join(MAIN_FOLDER, mainImage);
		const outputVideoName = `output_${i + 1}_${
			path.parse(mainImage).name
		}.mp4`;
		const outputVideoPath = path.join(OUTPUT_FOLDER, outputVideoName);

		console.log(
			`\n🔄 Processing ${i + 1}/${mainImages.length}: ${mainImage}`
		);

		try {
			await processSingleImage(
				mainImagePath,
				videoPath,
				outputVideoPath,
				i + 1
			);
		} catch (error) {
			console.error(`❌ Failed to process ${mainImage}:`, error.message);
			continue;
		}
	}

	console.log("\n✅ All main images processed!");
}

function processSingleImage(mainImagePath, videoPath, outputVideoPath, index) {
	return new Promise((resolve, reject) => {
		const jobName = `BatchSwapJob_${index}`;

		console.log(`🎭 Creating face swap job: ${jobName}`);

		// Create job
		const createJobCommand = [
			"python",
			"facefusion.py",
			"job-create",
			jobName,
		];

		// Add step
		const addStepCommand = [
			"python",
			"facefusion.py",
			"job-add-step",
			jobName,
			"-s",
			mainImagePath,
			"-t",
			videoPath,
			"-o",
			outputVideoPath,
			"--processors",
			"face_swapper",
			"face_enhancer",
			"--output-video-quality",
			"90",
		];

		// Submit job
		const submitJobCommand = [
			"python",
			"facefusion.py",
			"job-submit",
			jobName,
		];

		// Run job
		const runJobCommand = ["python", "facefusion.py", "job-run", jobName];

		try {
			console.log(`⚙️ Creating job...`);
			execSync(
				"source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh && conda activate facefusion && " +
					createJobCommand.join(" "),
				{ stdio: "inherit", shell: true }
			);

			console.log(`➕ Adding processing step...`);
			execSync(
				"source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh && conda activate facefusion && " +
					addStepCommand.join(" "),
				{ stdio: "inherit", shell: true }
			);

			console.log(`📤 Submitting job...`);
			execSync(
				"source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh && conda activate facefusion && " +
					submitJobCommand.join(" "),
				{ stdio: "inherit", shell: true }
			);

			console.log(`🏃 Running job...`);
			execSync(
				"source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh && conda activate facefusion && " +
					runJobCommand.join(" "),
				{ stdio: "inherit", shell: true }
			);

			console.log(`✅ Completed processing for image ${index}`);
			resolve();
		} catch (error) {
			console.error(`❌ Error in face swap process:`, error.message);
			reject(error);
		}
	});
}

// =========================================================
// 🖼️ STEP 3: EXTRACT FRAMES FROM VIDEOS
// =========================================================

async function extractFramesFromVideos() {
	console.log("📁 Reading output videos...");

	const videoFiles = fs
		.readdirSync(OUTPUT_FOLDER)
		.filter((file) => file.endsWith(".mp4"));

	if (videoFiles.length === 0) {
		throw new Error("No videos found in output folder!");
	}

	console.log(`🎞️ Found ${videoFiles.length} videos to process`);

	let totalFrameCount = 0;

	for (let i = 0; i < videoFiles.length; i++) {
		const videoFile = videoFiles[i];
		const videoPath = path.join(OUTPUT_FOLDER, videoFile);

		console.log(
			`\n🔍 Processing video ${i + 1}/${videoFiles.length}: ${videoFile}`
		);

		try {
			const frameCount = await extractFramesFromSingleVideo(
				videoPath,
				totalFrameCount
			);
			totalFrameCount += frameCount;
			console.log(`✅ Extracted ${frameCount} frames from ${videoFile}`);
		} catch (error) {
			console.error(
				`❌ Failed to extract frames from ${videoFile}:`,
				error.message
			);
			continue;
		}
	}

	console.log(`\n✅ Total frames extracted: ${totalFrameCount}`);
}

function extractFramesFromSingleVideo(videoPath, startFrameNumber) {
	return new Promise((resolve, reject) => {
		console.log(`🔍 Analyzing video: ${path.basename(videoPath)}...`);

		ffmpeg.ffprobe(videoPath, (err, metadata) => {
			if (err) {
				reject(err);
				return;
			}

			const videoStream = metadata.streams.find(
				(s) => s.codec_type === "video"
			);
			const fps = eval(videoStream.r_frame_rate);
			const width = videoStream.width;
			const height = videoStream.height;

			console.log(`📊 Video details: ${width}x${height} @ ${fps} FPS`);

			// Detect black bars with more aggressive settings
			console.log("🔍 Detecting black bars...");
			let cropValues = [];

			ffmpeg(videoPath)
				.outputOptions([`-vf cropdetect=24:2:0`, "-f null"])
				.on("stderr", (line) => {
					const match = line.match(/crop=(\d+:\d+:\d+:\d+)/);
					if (match) {
						const cropValue = match[1];
						cropValues.push(cropValue);
					}
				})
				.on("end", () => {
					let finalCrop = null;
					if (cropValues.length > 0) {
						// Find the most common crop value
						const cropCounts = {};
						cropValues.forEach((value) => {
							cropCounts[value] = (cropCounts[value] || 0) + 1;
						});

						let maxCount = 0;
						let bestCrop = null;
						for (const [crop, count] of Object.entries(
							cropCounts
						)) {
							if (count > maxCount) {
								maxCount = count;
								bestCrop = crop;
							}
						}

						// Parse crop values to find the one with largest area (least cropping)
						if (bestCrop) {
							const [w, h, x, y] = bestCrop
								.split(":")
								.map(Number);

							// Only use crop if it actually removes significant black bars
							// (more than 5% of width or height)
							const widthReduction = (width - w) / width;
							const heightReduction = (height - h) / height;

							if (
								widthReduction > 0.05 ||
								heightReduction > 0.05
							) {
								finalCrop = bestCrop;
								console.log(
									`✅ Using crop: ${finalCrop} (removes ${(
										widthReduction * 100
									).toFixed(1)}% width, ${(
										heightReduction * 100
									).toFixed(1)}% height)`
								);
							} else {
								console.log(
									`ℹ️ Minimal black bars detected, keeping original dimensions`
								);
							}
						}
					}

					console.log(
						"🚀 Extracting frames with optimized cropping..."
					);

					let filterOptions = `fps=${fps}`;
					if (finalCrop) {
						filterOptions += `,crop=${finalCrop}`;
					}

					// Use continuous numbering across all videos
					const outputPattern = path.join(
						EXTRACTED_FRAMES_FOLDER,
						`frame_${String(startFrameNumber + 1).padStart(
							6,
							"0"
						)}_%03d.jpg`
					);

					let frameCount = 0;
					ffmpeg(videoPath)
						.outputOptions([
							`-vf ${filterOptions}`,
							"-vsync 0",
							"-q:v 0",
						])
						.output(outputPattern)
						.on("progress", (progress) => {
							if (progress.percent) {
								process.stdout.write(
									`⏳ Extraction Progress: ${Math.round(
										progress.percent
									)}%\r`
								);
							}
						})
						.on("end", () => {
							// Count extracted frames
							const extractedFrames = fs
								.readdirSync(EXTRACTED_FRAMES_FOLDER)
								.filter((file) =>
									file.startsWith(
										`frame_${String(
											startFrameNumber + 1
										).padStart(6, "0")}`
									)
								);

							frameCount = extractedFrames.length;
							console.log(`\n✅ Frames extracted: ${frameCount}`);
							resolve(frameCount);
						})
						.on("error", (err) => reject(err))
						.run();
				})
				.on("error", (err) => reject(err))
				.save("pipe:1");
		});
	});
}

// =========================================================
// 🧹 STEP 4: CLEANUP
// =========================================================

async function cleanup(sourceVideoPath) {
	console.log("🗑️ Cleaning up temporary files...");

	try {
		// Delete source video from files folder
		if (fs.existsSync(sourceVideoPath)) {
			fs.unlinkSync(sourceVideoPath);
			console.log("✅ Source video deleted");
		}

		// Delete all videos from output folder (keep only extracted frames)
		const videoFiles = fs
			.readdirSync(OUTPUT_FOLDER)
			.filter((file) => file.endsWith(".mp4"));

		videoFiles.forEach((videoFile) => {
			const videoPath = path.join(OUTPUT_FOLDER, videoFile);
			fs.unlinkSync(videoPath);
		});

		if (videoFiles.length > 0) {
			console.log(`✅ ${videoFiles.length} output videos deleted`);
		}

		// Delete all face fusion jobs
		try {
			console.log("🗑️ Cleaning up face fusion jobs...");
			execSync(
				"source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh && conda activate facefusion && python facefusion.py job-delete-all",
				{ stdio: "inherit", shell: true }
			);
			console.log("✅ All face fusion jobs deleted");
		} catch (error) {
			console.warn(
				"⚠️ Could not delete face fusion jobs:",
				error.message
			);
		}
	} catch (error) {
		console.error("⚠️ Cleanup error:", error.message);
	}
}

// =========================================================
// 🎬 START PIPELINE
// =========================================================

main().catch((error) => {
	console.error("💥 Fatal error:", error.message);
	process.exit(1);
});
