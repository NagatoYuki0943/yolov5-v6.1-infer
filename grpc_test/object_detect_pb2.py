# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: object_detect.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13object_detect.proto\x12\robject_detect\"\x18\n\x07Request\x12\r\n\x05image\x18\x01 \x01(\t\")\n\x08Response\x12\r\n\x05image\x18\x01 \x01(\t\x12\x0e\n\x06\x64\x65tect\x18\x02 \x01(\t2L\n\nYoloDetect\x12>\n\tv5_detect\x12\x16.object_detect.Request\x1a\x17.object_detect.Response\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'object_detect_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _REQUEST._serialized_start=38
  _REQUEST._serialized_end=62
  _RESPONSE._serialized_start=64
  _RESPONSE._serialized_end=105
  _YOLODETECT._serialized_start=107
  _YOLODETECT._serialized_end=183
# @@protoc_insertion_point(module_scope)
