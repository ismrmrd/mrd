% This file was generated by the "yardl" tool. DO NOT EDIT.

classdef AcquisitionHeader < handle
  properties
    % A bit mask of common attributes applicable to individual acquisition
    flags
    % Encoding loop counters
    idx
    % Unique ID corresponding to the readout
    measurement_uid
    % Zero-indexed incrementing counter for readouts
    scan_counter
    % Clock time stamp (e.g. milliseconds since midnight)
    acquisition_time_stamp
    % Time stamps relative to physiological triggering
    physiology_time_stamp
    % Channel numbers
    channel_order
    % Number of readout samples to be discarded at the beginning
    %   (e.g. if the ADC is active during gradient events)
    discard_pre
    % Number of readout samples to be discarded at the end
    %   (e.g. if the ADC is active during gradient events)
    discard_post
    % Index of the readout sample corresponing to k-space center (zero indexed)
    center_sample
    % Indexed reference to the encoding spaces enumerated in the MRD Header
    encoding_space_ref
    % Readout bandwidth, as time between samples in microseconds
    sample_time_us
    % Center of the excited volume, in LPS coordinates relative to isocenter in millimeters
    position
    % Directional cosine of readout/frequency encoding
    read_dir
    % Directional cosine of phase encoding (2D)
    phase_dir
    % Directional cosine of slice normal, i.e. cross-product of read_dir and phase_dir
    slice_dir
    % Offset position of the patient table, in LPS coordinates
    patient_table_position
    % User-defined integer parameters
    user_int
    % User-defined float parameters
    user_float
  end

  methods
    function self = AcquisitionHeader(kwargs)
      arguments
        kwargs.flags = mrd.AcquisitionFlags(0);
        kwargs.idx = mrd.EncodingCounters();
        kwargs.measurement_uid = uint32(0);
        kwargs.scan_counter = yardl.None;
        kwargs.acquisition_time_stamp = yardl.None;
        kwargs.physiology_time_stamp = uint32.empty();
        kwargs.channel_order = uint32.empty();
        kwargs.discard_pre = yardl.None;
        kwargs.discard_post = yardl.None;
        kwargs.center_sample = yardl.None;
        kwargs.encoding_space_ref = yardl.None;
        kwargs.sample_time_us = yardl.None;
        kwargs.position = repelem(single(0), 3, 1);
        kwargs.read_dir = repelem(single(0), 3, 1);
        kwargs.phase_dir = repelem(single(0), 3, 1);
        kwargs.slice_dir = repelem(single(0), 3, 1);
        kwargs.patient_table_position = repelem(single(0), 3, 1);
        kwargs.user_int = int32.empty();
        kwargs.user_float = single.empty();
      end
      self.flags = kwargs.flags;
      self.idx = kwargs.idx;
      self.measurement_uid = kwargs.measurement_uid;
      self.scan_counter = kwargs.scan_counter;
      self.acquisition_time_stamp = kwargs.acquisition_time_stamp;
      self.physiology_time_stamp = kwargs.physiology_time_stamp;
      self.channel_order = kwargs.channel_order;
      self.discard_pre = kwargs.discard_pre;
      self.discard_post = kwargs.discard_post;
      self.center_sample = kwargs.center_sample;
      self.encoding_space_ref = kwargs.encoding_space_ref;
      self.sample_time_us = kwargs.sample_time_us;
      self.position = kwargs.position;
      self.read_dir = kwargs.read_dir;
      self.phase_dir = kwargs.phase_dir;
      self.slice_dir = kwargs.slice_dir;
      self.patient_table_position = kwargs.patient_table_position;
      self.user_int = kwargs.user_int;
      self.user_float = kwargs.user_float;
    end

    function res = eq(self, other)
      res = ...
        isa(other, "mrd.AcquisitionHeader") && ...
        isequal(self.flags, other.flags) && ...
        isequal(self.idx, other.idx) && ...
        isequal(self.measurement_uid, other.measurement_uid) && ...
        isequal(self.scan_counter, other.scan_counter) && ...
        isequal(self.acquisition_time_stamp, other.acquisition_time_stamp) && ...
        isequal(self.physiology_time_stamp, other.physiology_time_stamp) && ...
        isequal(self.channel_order, other.channel_order) && ...
        isequal(self.discard_pre, other.discard_pre) && ...
        isequal(self.discard_post, other.discard_post) && ...
        isequal(self.center_sample, other.center_sample) && ...
        isequal(self.encoding_space_ref, other.encoding_space_ref) && ...
        isequal(self.sample_time_us, other.sample_time_us) && ...
        isequal(self.position, other.position) && ...
        isequal(self.read_dir, other.read_dir) && ...
        isequal(self.phase_dir, other.phase_dir) && ...
        isequal(self.slice_dir, other.slice_dir) && ...
        isequal(self.patient_table_position, other.patient_table_position) && ...
        isequal(self.user_int, other.user_int) && ...
        isequal(self.user_float, other.user_float);
    end

    function res = ne(self, other)
      res = ~self.eq(other);
    end
  end

  methods (Static)
    function z = zeros(varargin)
      elem = mrd.AcquisitionHeader();
      if nargin == 0
        z = elem;
        return;
      end
      sz = [varargin{:}];
      if isscalar(sz)
        sz = [sz, sz];
      end
      z = reshape(repelem(elem, prod(sz)), sz);
    end
  end
end
