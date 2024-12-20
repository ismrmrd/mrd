% This file was generated by the "yardl" tool. DO NOT EDIT.

classdef SamplingLimitsSerializer < yardl.binary.RecordSerializer
  methods
    function self = SamplingLimitsSerializer()
      field_serializers{1} = mrd.binary.LimitTypeSerializer();
      field_serializers{2} = mrd.binary.LimitTypeSerializer();
      field_serializers{3} = mrd.binary.LimitTypeSerializer();
      self@yardl.binary.RecordSerializer('mrd.SamplingLimits', field_serializers);
    end

    function write(self, outstream, value)
      arguments
        self
        outstream (1,1) yardl.binary.CodedOutputStream
        value (1,1) mrd.SamplingLimits
      end
      self.write_(outstream, value.kspace_encoding_step_0, value.kspace_encoding_step_1, value.kspace_encoding_step_2);
    end

    function value = read(self, instream)
      fields = self.read_(instream);
      value = mrd.SamplingLimits(kspace_encoding_step_0=fields{1}, kspace_encoding_step_1=fields{2}, kspace_encoding_step_2=fields{3});
    end
  end
end
