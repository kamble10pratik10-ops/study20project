import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException, status
from config import get_settings
import io

settings = get_settings()

# Configure Cloudinary
cloudinary.config(
    cloud_name="dsy0u40lh",
    api_key="993628589566454",
    api_secret="uqOyjfE3FLHmMLaoj9i9LTGfBq4",
)


async def upload_file_to_cloudinary(
    file: UploadFile,
    folder: str = "posts"
) -> dict:
    """
    Upload a file to Cloudinary and return the upload result.
    
    Args:
        file: FastAPI UploadFile object
        folder: Cloudinary folder to store the file in
        
    Returns:
        dict: Cloudinary upload result containing 'secure_url', 'public_id', etc.
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Reset file pointer for potential reuse
        await file.seek(0)
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            io.BytesIO(file_content),
            folder=folder,
            resource_type="auto",  # Auto-detect: image, video, raw (for PDFs)
            use_filename=True,
            unique_filename=True,
            upload_preset= "ml_default",
            type= "upload",
            public_id="26cff044-abd1-4baa-bf94-083165b2aefd",
        )

        
        return upload_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to Cloudinary: {str(e)}"
        )


def delete_file_from_cloudinary(public_id: str, resource_type: str = "auto") -> dict:
    """
    Delete a file from Cloudinary.
    
    Args:
        public_id: Cloudinary public_id of the file to delete
        resource_type: Type of resource ('image', 'video', 'raw', 'auto')
        
    Returns:
        dict: Cloudinary delete result
    """
    try:
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type=resource_type
        )
        return result
    except Exception as e:
        # Log error but don't raise exception - file might already be deleted
        print(f"Error deleting file from Cloudinary: {str(e)}")
        return {"result": "error", "message": str(e)}


def extract_public_id_from_url(url: str) -> str:
    """
    Extract public_id from Cloudinary URL.
    
    Args:
        url: Cloudinary URL (e.g., https://res.cloudinary.com/cloud_name/image/upload/v1234567890/folder/filename.jpg)
        
    Returns:
        str: public_id (e.g., folder/filename)
    """
    try:
        # Cloudinary URLs have the format:
        # https://res.cloudinary.com/{cloud_name}/{resource_type}/upload/{version}/{public_id}.{format}
        # We need to extract the public_id part
        
        # Split by '/upload/'
        if '/upload/' in url:
            parts = url.split('/upload/')
            if len(parts) > 1:
                # Get everything after /upload/
                after_upload = parts[1]
                # Remove version if present (format: v1234567890/folder/filename.ext)
                if '/' in after_upload:
                    # Split by '/' and skip the first part if it starts with 'v' (version)
                    path_parts = after_upload.split('/')
                    if path_parts[0].startswith('v') and path_parts[0][1:].isdigit():
                        # Skip version
                        public_id = '/'.join(path_parts[1:])
                    else:
                        public_id = after_upload
                    
                    # Remove file extension
                    if '.' in public_id:
                        public_id = public_id.rsplit('.', 1)[0]
                    
                    return public_id
        
        # Fallback: try to extract from URL directly
        # If URL doesn't match expected format, return as is
        return url
    except Exception as e:
        print(f"Error extracting public_id from URL: {str(e)}")
        return url





