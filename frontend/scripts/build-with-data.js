const { execSync } = require('child_process');
const fs = require('fs-extra');
const path = require('path');

console.log('🚀 Starting complete build process...\n');

// Paths
const projectRoot = path.join(__dirname, '..', '..');
const pythonScript = path.join(projectRoot, 'generate_static_data_enhanced.py');
// const pythonScript = path.join(projectRoot, 'generate_static_data.py');
const sourceDir = path.join(projectRoot, 'public_data');
const targetDir = path.join(__dirname, '..', 'build', 'data');

// Step 1: Run Python script to generate fresh data
console.log('📊 Step 1: Generating fresh SEC data...');
console.log('   Running:', pythonScript);

try {
  // Check if Python script exists
  if (!fs.existsSync(pythonScript)) {
    console.log('⚠️  Warning: generate_static_data.py not found at project root');
    console.log('   Expected location:', pythonScript);
    console.log('   Skipping data generation...\n');
  } else {
    // Run the Python script
    execSync(`python "${pythonScript}"`, {
      cwd: projectRoot,
      stdio: 'inherit' // Show Python script output in console
    });
    console.log('✅ Data generation complete!\n');
  }
} catch (error) {
  console.error('❌ Error running Python script:');
  console.error(error.message);
  console.log('\n⚠️  Continuing with existing data (if available)...\n');
}

// Step 2: Build React app
console.log('⚛️  Step 2: Building React application...');
console.log('   Running: craco build\n');

try {
  execSync('npm run build:react', {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit'
  });
  console.log('\n✅ React build complete!\n');
} catch (error) {
  console.error('❌ Error building React app:');
  console.error(error.message);
  process.exit(1);
}

// Step 3: Copy data folder to build
console.log('📦 Step 3: Copying data to build folder...');
console.log('   Source:', sourceDir);
console.log('   Target:', targetDir);

try {
  // Check if source exists
  if (!fs.existsSync(sourceDir)) {
    console.log('\n⚠️  Warning: public_data folder not found');
    console.log('   Expected at:', sourceDir);
    console.log('   Build will not include data files.\n');
    process.exit(0);
  }

  // Remove old data folder if exists
  if (fs.existsSync(targetDir)) {
    fs.removeSync(targetDir);
  }

  // Copy public_data to build/data
  fs.copySync(sourceDir, targetDir);
  
  // Verify files were copied
  const files = fs.readdirSync(targetDir);
  console.log(`\n✅ Successfully copied ${files.length} files to build/data:`);
  files.forEach(file => {
    const stats = fs.statSync(path.join(targetDir, file));
    const sizeKB = (stats.size / 1024).toFixed(2);
    console.log(`   - ${file} (${sizeKB} KB)`);
  });
  
} catch (error) {
  console.error('\n❌ Error copying data folder:');
  console.error(error.message);
  process.exit(1);
}

console.log('\n🎉 Complete build process finished successfully!');
console.log('📁 Your build folder is ready to deploy!\n');