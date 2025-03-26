// 依赖项更新脚本
// 此脚本用于将所有前端依赖更新到最新版本

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 最新版本信息 (基于分析报告)
const latestVersions = {
    // 核心依赖
    'vue': '^3.5.13',
    'pinia': '^3.0.1',
    'vue-router': '^4.5.0',
    'ant-design-vue': '^4.2.6',
    'typescript': '^5.8.2',

    // 构建工具
    'vite': '^6.2.2',
    'vue-tsc': '^2.2.8',

    // ESLint相关
    '@typescript-eslint/eslint-plugin': '^8.27.0',
    '@typescript-eslint/parser': '^8.26.1',
    '@vitejs/plugin-vue': '^5.2.3',

    // 其他依赖(保持最新)
    'axios': '^1.6.7',
    'dayjs': '^1.11.10',
    'vue-i18n': '^9.9.0',
    '@types/node': '^20.11.24',
    'eslint': '^8.57.0',
    'eslint-plugin-vue': '^9.21.1',
    'sass': '^1.71.1',
    'vitest': '^1.3.1',
    'terser': '^5.28.0'
};

// 读取package.json
const packageJsonPath = path.resolve(__dirname, '../frontend/package.json');
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

// 更新依赖版本
let updated = false;
['dependencies', 'devDependencies'].forEach(depType => {
    if (packageJson[depType]) {
        Object.keys(packageJson[depType]).forEach(pkg => {
            if (latestVersions[pkg]) {
                const oldVersion = packageJson[depType][pkg];
                packageJson[depType][pkg] = latestVersions[pkg];
                console.log(`更新 ${pkg}: ${oldVersion} -> ${latestVersions[pkg]}`);
                updated = true;
            }
        });
    }
});

// 写入更新后的package.json
if (updated) {
    fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
    console.log('package.json 已更新，现在运行 npm install 以应用更改...');

    try {
        // 切换到frontend目录并运行npm install
        process.chdir(path.resolve(__dirname, '../frontend'));
        console.log('正在安装更新的依赖...');
        execSync('npm install', { stdio: 'inherit' });
        console.log('✅ 所有依赖已成功更新到最新版本！');
    } catch (error) {
        console.error('❌ 安装依赖时出错:', error.message);
    }
} else {
    console.log('没有需要更新的依赖');
}