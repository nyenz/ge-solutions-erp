import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

print("=== FIXING CLOUDINARY PDF UPLOADS ===")

filepath = 'erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LocalStorageServiceImpl.java'
data = read(filepath)

# 1. Change resource type detection for PDFs from "raw" to "image"
old_detection = """        if (contentType != null && contentType.equals("application/pdf")) return "raw";
        if (originalName.endsWith(".pdf")) return "raw";"""
new_detection = """        if (contentType != null && contentType.equals("application/pdf")) return "image";
        if (originalName.endsWith(".pdf")) return "image";"""
data = data.replace(old_detection, new_detection)

# 2. Add use_filename parameters to the upload map
old_upload = """        Map<?, ?> result = cloudinary.uploader().upload(
                verified.getBytes(),
                ObjectUtils.asMap(
                        "folder", "ge_solutions/" + folder,
                        "resource_type", resourceType,
                        "access_mode", "public"
                )
        );"""
new_upload = """        Map<?, ?> result = cloudinary.uploader().upload(
                verified.getBytes(),
                ObjectUtils.asMap(
                        "folder", "ge_solutions/" + folder,
                        "resource_type", resourceType,
                        "use_filename", true,
                        "unique_filename", true,
                        "access_mode", "public"
                )
        );"""
data = data.replace(old_upload, new_upload)

write(filepath, data)
print("=== DONE ===")