#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smoothstack Backend API Entry Point
"""

import os
import sys
import logging
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger("smoothstack")

# API Application
app = FastAPI(
    title="Smoothstack API",
    description="Smoothstack Backend API",
    version="0.1.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 文档目录配置
DOCS_DIR = Path(__file__).parent.parent / "docs"


# 文档路由
@app.get("/docs")
async def list_docs():
    """列出所有文档"""
    docs = []
    for file in DOCS_DIR.rglob("*.md"):
        relative_path = file.relative_to(DOCS_DIR)
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            title_match = next(
                (line for line in content.split("\n") if line.startswith("# ")), None
            )
            title = title_match[2:] if title_match else relative_path.stem
        docs.append(
            {
                "path": str(relative_path).replace("\\", "/").replace(".md", ""),
                "title": title,
            }
        )
    return docs


@app.get("/docs/{path:path}")
async def get_doc(path: str):
    """获取指定文档的内容"""
    file_path = DOCS_DIR / f"{path}.md"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"content": content}


# Health Check
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": os.getenv("ENV", "development"),
    }


# Error Handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"},
    )


@app.get("/")
async def root():
    return {"message": "Welcome to Smoothstack API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
