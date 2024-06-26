% This file was generated by the "yardl" tool. DO NOT EDIT.

classdef AcquisitionSystemInformationTypeSerializer < yardl.binary.RecordSerializer
  methods
    function self = AcquisitionSystemInformationTypeSerializer()
      field_serializers{1} = yardl.binary.OptionalSerializer(yardl.binary.StringSerializer);
      field_serializers{2} = yardl.binary.OptionalSerializer(yardl.binary.StringSerializer);
      field_serializers{3} = yardl.binary.OptionalSerializer(yardl.binary.Float32Serializer);
      field_serializers{4} = yardl.binary.OptionalSerializer(yardl.binary.Float32Serializer);
      field_serializers{5} = yardl.binary.OptionalSerializer(yardl.binary.Uint32Serializer);
      field_serializers{6} = yardl.binary.VectorSerializer(mrd.binary.CoilLabelTypeSerializer());
      field_serializers{7} = yardl.binary.OptionalSerializer(yardl.binary.StringSerializer);
      field_serializers{8} = yardl.binary.OptionalSerializer(yardl.binary.StringSerializer);
      field_serializers{9} = yardl.binary.OptionalSerializer(yardl.binary.StringSerializer);
      field_serializers{10} = yardl.binary.OptionalSerializer(yardl.binary.StringSerializer);
      self@yardl.binary.RecordSerializer('mrd.AcquisitionSystemInformationType', field_serializers);
    end

    function write(self, outstream, value)
      arguments
        self
        outstream (1,1) yardl.binary.CodedOutputStream
        value (1,1) mrd.AcquisitionSystemInformationType
      end
      self.write_(outstream, value.system_vendor, value.system_model, value.system_field_strength_t, value.relative_receiver_noise_bandwidth, value.receiver_channels, value.coil_label, value.institution_name, value.station_name, value.device_id, value.device_serial_number);
    end

    function value = read(self, instream)
      fields = self.read_(instream);
      value = mrd.AcquisitionSystemInformationType(system_vendor=fields{1}, system_model=fields{2}, system_field_strength_t=fields{3}, relative_receiver_noise_bandwidth=fields{4}, receiver_channels=fields{5}, coil_label=fields{6}, institution_name=fields{7}, station_name=fields{8}, device_id=fields{9}, device_serial_number=fields{10});
    end
  end
end
