% This file was generated by the "yardl" tool. DO NOT EDIT.

classdef KspaceSerializer < yardl.binary.RecordSerializer
  methods
    function self = KspaceSerializer()
      field_serializers{1} = mrd.binary.AcquisitionSerializer();
      field_serializers{2} = yardl.binary.NDArraySerializer(yardl.binary.Complexfloat32Serializer, 6);
      field_serializers{3} = yardl.binary.OptionalSerializer(yardl.binary.NDArraySerializer(yardl.binary.BoolSerializer, 4));
      self@yardl.binary.RecordSerializer('mrd.Kspace', field_serializers);
    end

    function write(self, outstream, value)
      arguments
        self
        outstream (1,1) yardl.binary.CodedOutputStream
        value (1,1) mrd.Kspace
      end
      self.write_(outstream, value.reference, value.data, value.mask);
    end

    function value = read(self, instream)
      fields = self.read_(instream);
      value = mrd.Kspace(reference=fields{1}, data=fields{2}, mask=fields{3});
    end
  end
end