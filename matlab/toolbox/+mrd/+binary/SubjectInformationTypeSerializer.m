% This file was generated by the "yardl" tool. DO NOT EDIT.

classdef SubjectInformationTypeSerializer < yardl.binary.RecordSerializer
  methods
    function self = SubjectInformationTypeSerializer()
      field_serializers{1} = yardl.binary.OptionalSerializer(yardl.binary.StringSerializer);
      field_serializers{2} = yardl.binary.OptionalSerializer(yardl.binary.Float32Serializer);
      field_serializers{3} = yardl.binary.OptionalSerializer(yardl.binary.Float32Serializer);
      field_serializers{4} = yardl.binary.OptionalSerializer(yardl.binary.StringSerializer);
      field_serializers{5} = yardl.binary.OptionalSerializer(yardl.binary.DateSerializer);
      field_serializers{6} = yardl.binary.OptionalSerializer(yardl.binary.EnumSerializer('mrd.PatientGender', @mrd.PatientGender, yardl.binary.Int32Serializer));
      self@yardl.binary.RecordSerializer('mrd.SubjectInformationType', field_serializers);
    end

    function write(self, outstream, value)
      arguments
        self
        outstream (1,1) yardl.binary.CodedOutputStream
        value (1,1) mrd.SubjectInformationType
      end
      self.write_(outstream, value.patient_name, value.patient_weight_kg, value.patient_height_m, value.patient_id, value.patient_birthdate, value.patient_gender);
    end

    function value = read(self, instream)
      fields = self.read_(instream);
      value = mrd.SubjectInformationType(patient_name=fields{1}, patient_weight_kg=fields{2}, patient_height_m=fields{3}, patient_id=fields{4}, patient_birthdate=fields{5}, patient_gender=fields{6});
    end
  end
end
