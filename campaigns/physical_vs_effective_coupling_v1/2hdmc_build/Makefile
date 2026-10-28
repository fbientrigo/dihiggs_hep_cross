# Makefile for 2HDMC

# Choose your C++ compiler here (in general g++ on Linux systems):
CC = g++
LDFLAGS=-fopenmp -lgsl -lgslcblas


#Optimisation level, eg: -O3
OPT=-O3
#OR debug level: -g(n=1,2,3)
DEBUG=

VPATH=src

CFLAGS= -std=c++11 -Wall $(DEBUG) $(OPT) -fopenmp -MMD -MP

OBJDIR=lib
LIBDIR=$(OBJDIR)
SOURCES=THDM.cpp SM.cpp DecayTable.cpp Constraints.cpp Util.cpp
OBJECTS=$(SOURCES:.cpp=.o)
LIB=lib2HDMC.a
LDFLAGS+=-L$(LIBDIR) -l2HDMC -lgsl -lgslcblas -lm
#LDFLAGS+=-L$(LIBDIR) -l2HDMC
LIBS=
PROG=CalcPhys CalcGen CalcHiggs CalcHybrid CalcHMSSM CalcMSSM CalcInert CalcLH Demo CalcRoundTrip CalcLam1Scan CalcLam1ScanFromLake
INCLUDE=

# To use HiggsBounds/HiggsSignals for Higgs constraints, set both of the
# following path variables to the corresponding build directories.
# Requires HiggsBounds>=5.7.0 and HiggsSignals>=2.4.0
# HiggsBounds_DIR="path-to"/HiggsBounds/higgsbounds-5.7.0/build
# HiggsSignals_DIR="path-to"/HiggsSignals/higgssignals-2.4.0/build

ifdef HiggsBounds_DIR
ifdef HiggsSignals_DIR
CFLAGS+=-DHiggsBounds
LDFLAGS+=-L$(HiggsBounds_DIR)/lib -L$(HiggsSignals_DIR)/lib -lHS -lHB -lgfortran
INCLUDE+=-I$(HiggsBounds_DIR)/../include -I$(HiggsSignals_DIR)/../include
SOURCES+=HBHS.cpp
endif
endif


#CFLAGS+=-DHiggsBounds
#LDFLAGS+=-L$(LIBDIR) -lHS -lHB -lgfortran
#SOURCES+=HBHS.cpp

.PHONY: lib clean distclean

all: lib $(PROG)

# NOTE: this rule used to be "%.cpp %.h" -- i.e. each object file depended
# only on its OWN matching header, not on any header it transitively
# #include's. THDM.cpp/DecayTable.cpp/Constraints.cpp/etc all #include
# THDM.h, so when THDM.h's class layout changed, an incremental `make`
# left DecayTable.o/Constraints.o/SM.o/Util.o compiled against the OLD
# layout while THDM.o got the new one -- linking them into one lib2HDMC.a
# is a real ODR violation (silently wrong output, no compiler warning).
# See campaigns/physical_vs_effective_coupling_v1/validation/
# MASS_RECONSTRUCTION_FIX.md in dihiggs_hep_cross for the incident this
# caused. -MMD -MP (CFLAGS above) makes each compile also emit a .d file
# with the FULL transitive #include graph; -include below makes Make
# actually use those on every subsequent build, so this class of bug is no
# longer possible from a plain `make` -- only the first build after a
# clean checkout needs `make clean` to be safe (no .d files exist yet).
$(OBJDIR)/%.o : %.cpp
	@mkdir -p $(OBJDIR)
	$(CC) $(CFLAGS) $(INCLUDE) -c $< -o $@

-include $(addprefix $(OBJDIR)/, $(OBJECTS:.o=.d))

lib: $(addprefix $(LIBDIR)/, $(LIB))

$(addprefix $(LIBDIR)/, $(LIB)): $(addprefix $(OBJDIR)/, $(OBJECTS))
	@ echo "Making library $@"
	@ ar rcs $@ $(addprefix $(OBJDIR)/, $(OBJECTS))

%: %.cpp $(addprefix $(LIBDIR)/, $(LIB))
	@ echo $(CC) $< -Isrc $(CFLAGS) $(LDFLAGS) $(addprefix $(LIBDIR)/, $(LIBS)) -o $@
	@ $(CC) $< -Isrc $(CFLAGS) $(LDFLAGS) $(addprefix $(LIBDIR)/, $(LIBS)) -o $@

clean:
	@ echo "Cleaning library"
	@ rm -f $(addprefix $(OBJDIR)/, *.o)
	@ rm -f $(addprefix $(OBJDIR)/, *.d)
	@ rm -f $(addprefix $(LIBDIR)/, $(LIB))

distclean:
	@ make -s clean
	@ echo "Cleaning programs"
	@ rm -f $(PROG)
