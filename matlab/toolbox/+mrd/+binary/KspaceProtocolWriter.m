% This file was generated by the "yardl" tool. DO NOT EDIT.

classdef KspaceProtocolWriter < yardl.binary.BinaryProtocolWriter & mrd.KspaceProtocolWriterBase
  % Binary writer for the KspaceProtocol protocol
  properties (Access=protected)
    header_serializer
    kspace_serializer
  end

  methods
    function self = KspaceProtocolWriter(filename)
      self@mrd.KspaceProtocolWriterBase();
      self@yardl.binary.BinaryProtocolWriter(filename, mrd.KspaceProtocolWriterBase.schema);
      self.header_serializer = yardl.binary.OptionalSerializer(mrd.binary.HeaderSerializer());
      self.kspace_serializer = yardl.binary.StreamSerializer(mrd.binary.KspaceSerializer());
    end
  end

  methods (Access=protected)
    function write_header_(self, value)
      self.header_serializer.write(self.stream_, value);
    end

    function write_kspace_(self, value)
      self.kspace_serializer.write(self.stream_, value);
    end
  end
end