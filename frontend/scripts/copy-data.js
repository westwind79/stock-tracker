const fs = require('fs-extra');
const path = require('path');

// Paths
const sourceDir = path.join(__dirname, '..', '..', 'public_data');
const targetDir = path.join(__dirname, '..', 'build', 'data');

console.log('📦 Post-build: Copying public_data to build/data...');
console.log('   Looking for data at:', sourceDir);

// Check if source exists
if (!fs.existsSync(sourceDir)) {
  console.log('⚠️  Warning: public_data folder not found at project root.');
  console.log('   Create it by running: python generate_static_data.py');
  console.log('   Skipping data copy...');
  process.exit(0);
}

// Copy the folder
try {
  // Remove old data folder if exists
  if (fs.existsSync(targetDir)) {
    fs.removeSync(targetDir);
    console.log('   Removed old data folder');
  }

  // Copy public_data to build/data
  fs.copySync(sourceDir, targetDir);
  
  // Verify files were copied
  const files = fs.readdirSync(targetDir);
  console.log(`✅ Successfully copied ${files.length} files to build/data:`);
  files.forEach(file => {
    const stats = fs.statSync(path.join(targetDir, file));
    const sizeKB = (stats.size / 1024).toFixed(2);
    console.log(`   - ${file} (${sizeKB} KB)`);
  });
  
} catch (error) {
  console.error('❌ Error copying public_data folder:');
  console.error(error.message);
  process.exit(1);
}

console.log('🎉 Build complete with data files!');