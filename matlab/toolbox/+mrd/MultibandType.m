% This file was generated by the "yardl" tool. DO NOT EDIT.

classdef MultibandType < handle
  properties
    spacing
    delta_kz
    multiband_factor
    calibration
    calibration_encoding
  end

  methods
    function self = MultibandType(kwargs)
      arguments
        kwargs.spacing = mrd.MultibandSpacingType.empty();
        kwargs.delta_kz = single(0);
        kwargs.multiband_factor = uint32(0);
        kwargs.calibration = mrd.Calibration.SEPARABLE_2D;
        kwargs.calibration_encoding = uint64(0);
      end
      self.spacing = kwargs.spacing;
      self.delta_kz = kwargs.delta_kz;
      self.multiband_factor = kwargs.multiband_factor;
      self.calibration = kwargs.calibration;
      self.calibration_encoding = kwargs.calibration_encoding;
    end

    function res = eq(self, other)
      res = ...
        isa(other, "mrd.MultibandType") && ...
        isequal(self.spacing, other.spacing) && ...
        isequal(self.delta_kz, other.delta_kz) && ...
        isequal(self.multiband_factor, other.multiband_factor) && ...
        isequal(self.calibration, other.calibration) && ...
        isequal(self.calibration_encoding, other.calibration_encoding);
    end

    function res = ne(self, other)
      res = ~self.eq(other);
    end
  end

  methods (Static)
    function z = zeros(varargin)
      elem = mrd.MultibandType();
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
