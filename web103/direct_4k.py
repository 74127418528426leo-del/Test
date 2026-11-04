#!/usr/bin/env python3
"""Official Pexels Free download redirect to the original 3840x2160 MP4.
This is separate from the Pexels web preview player's chosen resolution.
Run in actual unchanged Puppy50 Firefox via web102 QMP evidence harness.
"""
from web102 import pexels_kvm
DIRECT_MP4="https://videos.pexels.com/video-files/27251986/12102943_3840_2160_30fps.mp4"
pexels_kvm.URL=DIRECT_MP4
if __name__=="__main__":
    pexels_kvm.main()
