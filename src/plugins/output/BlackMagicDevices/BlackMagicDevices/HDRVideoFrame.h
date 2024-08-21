/* -LICENSE-START-
** Copyright (c) 2024 Blackmagic Design
**  
** Permission is hereby granted, free of charge, to any person or organization 
** obtaining a copy of the software and accompanying documentation (the 
** "Software") to use, reproduce, display, distribute, sub-license, execute, 
** and transmit the Software, and to prepare derivative works of the Software, 
** and to permit third-parties to whom the Software is furnished to do so, in 
** accordance with:
** 
** (1) if the Software is obtained from Blackmagic Design, the End User License 
** Agreement for the Software Development Kit ("EULA") available at 
** https://www.blackmagicdesign.com/EULA/DeckLinkSDK; or
** 
** (2) if the Software is obtained from any third party, such licensing terms 
** as notified by that third party,
** 
** and all subject to the following:
** 
** (3) the copyright notices in the Software and this entire statement, 
** including the above license grant, this restriction and the following 
** disclaimer, must be included in all copies of the Software, in whole or in 
** part, and all derivative works of the Software, unless such copies or 
** derivative works are solely in the form of machine-executable object code 
** generated by a source language processor.
** 
** (4) THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
** OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
** FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT 
** SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE 
** FOR ANY DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE, 
** ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
** DEALINGS IN THE SOFTWARE.
** 
** A copy of the Software is available free of charge at 
** https://www.blackmagicdesign.com/desktopvideo_sdk under the EULA.
** 
** -LICENSE-END-
*/
//
// HDRVideoFrame.h
//

#pragma once

#include <DeckLinkAPI.h>

#ifdef PLATFORM_LINUX
typedef const char* IDeckLinkVideoFrameMetadataExtensions_GetStringValueType;
typedef bool IDeckLinkVideoFrameMetadataExtensions_GetFlagValueType;
#endif

#ifdef PLATFORM_WINDOWS
typedef BSTR IDeckLinkVideoFrameMetadataExtensions_GetStringValueType;
typedef BOOL IDeckLinkVideoFrameMetadataExtensions_GetFlagValueType;
#endif

#ifdef PLATFORM_DARWIN
typedef CFStringRef IDeckLinkVideoFrameMetadataExtensions_GetStringValueType;
typedef bool IDeckLinkVideoFrameMetadataExtensions_GetFlagValueType;
#endif

#include <stdint.h>
#include <atomic>
#include <memory>
#include <string>

struct ChromaticityCoordinates
{
  double RedX{ 0.0 };
  double RedY{ 0.0 };
  double GreenX{ 0.0 };
  double GreenY{ 0.0 };
  double BlueX{ 0.0 };
  double BlueY{ 0.0 };
  double WhiteX{ 0.0 };
  double WhiteY{ 0.0 };
};

struct HDRMetadata
{
  ChromaticityCoordinates referencePrimaries;
  double minDisplayMasteringLuminance{ 0.0 };
  double maxDisplayMasteringLuminance{ 0.0 };
  double maxContentLightLevel{ 0.0 };
  double maxFrameAverageLightLevel{ 0.0 };
  int64_t electroOpticalTransferFunction{ 0 };
};

class HDRVideoFrame : public IDeckLinkVideoFrame,
                      public IDeckLinkVideoFrameMetadataExtensions
{
 public:
  HDRVideoFrame( IDeckLinkMutableVideoFrame* frame );
  virtual ~HDRVideoFrame() {}

  // IUnknown interface
  virtual HRESULT QueryInterface( REFIID iid, LPVOID* ppv );
  virtual ULONG AddRef( void );
  virtual ULONG Release( void );

  // IDeckLinkVideoFrame interface
  virtual long GetWidth( void )
  {
    return m_videoFrame->GetWidth();
  }
  virtual long GetHeight( void )
  {
    return m_videoFrame->GetHeight();
  }
  virtual long GetRowBytes( void )
  {
    return m_videoFrame->GetRowBytes();
  }
  virtual BMDPixelFormat GetPixelFormat( void )
  {
    return m_videoFrame->GetPixelFormat();
  }
  virtual BMDFrameFlags GetFlags( void )
  {
    return m_videoFrame->GetFlags() | bmdFrameContainsHDRMetadata;
  }
  virtual HRESULT GetBytes( void** buffer )
  {
    return m_videoFrame->GetBytes( buffer );
  }
  virtual HRESULT GetTimecode( BMDTimecodeFormat format,
                               IDeckLinkTimecode** timecode )
  {
    return m_videoFrame->GetTimecode( format, timecode );
  }
  virtual HRESULT GetAncillaryData( IDeckLinkVideoFrameAncillary** ancillary )
  {
    return m_videoFrame->GetAncillaryData( ancillary );
  }

  // IDeckLinkVideoFrameMetadataExtensions interface
  virtual HRESULT GetInt( BMDDeckLinkFrameMetadataID metadataID,
                          int64_t* value );
  virtual HRESULT GetFloat( BMDDeckLinkFrameMetadataID metadataID,
                            double* value );
  virtual HRESULT GetFlag(
      BMDDeckLinkFrameMetadataID metadataID,
      IDeckLinkVideoFrameMetadataExtensions_GetFlagValueType* value );
  virtual HRESULT GetString(
      BMDDeckLinkFrameMetadataID metadataID,
      IDeckLinkVideoFrameMetadataExtensions_GetStringValueType* value );
  virtual HRESULT GetBytes( BMDDeckLinkFrameMetadataID metadataID, void* buffer,
                            uint32_t* bufferSize );

  static std::string DumpHDRMetadata();
  static void SetHDRMetadata( const HDRMetadata& metadata )
  {
    s_metadata = metadata;
  }

  // Set the HDR metadata after parsing the HDR metadata passed as comma
  // separated values in a string Returns false if parsing error, true if
  // sucessful
  static bool SetHDRMetadata( const std::string& data );

 private:
  IDeckLinkMutableVideoFrame* m_videoFrame;
  static HDRMetadata s_metadata;
  std::atomic<ULONG> m_refCount;
};
