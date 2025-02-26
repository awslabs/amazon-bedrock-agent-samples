## Simulate camera streams

This container sets up 4 simulated camera streams from a house. A 3 minute video for camera stream is used in a loop, continuously writing streaming data to Kinesis Video Stream to simulate the cameras from a house.

The sample uses the [Kinesis Video Streams producer SDK for C++](https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp), which build a KVS sink for a GStreamer pipeline. As part of the SDK, there are example C++ programs that setrs up GStreamer piipelines for different sources, like connected cameras, RTSP streams or mp4 files. You can read more about how to use the included samples and use with your own real-time cameras in the SDK on the SDK github.
