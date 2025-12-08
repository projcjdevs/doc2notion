import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  ScrollView,
  Animated,
  Platform,
  Alert,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import * as DocumentPicker from 'expo-document-picker';
import axios from 'axios';
import { SafeAreaView } from 'react-native-safe-area-context';

const API_URL = 'http://192.168.100.20:8000';

export default function UploadScreen() {
  const [image, setImage] = useState<string | null>(null);
  const [document, setDocument] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [uploadProgress] = useState(new Animated.Value(0));

  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });

    if (!result.canceled) {
      setImage(result.assets[0].uri);
      setDocument(null);
      setResult(null);
    }
  };

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      quality: 0.8,
    });

    if (!result.canceled) {
      setImage(result.assets[0].uri);
      setDocument(null);
      setResult(null);
    }
  };

  const pickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/*'],
        copyToCacheDirectory: true,
      });

      if (!result.canceled) {
        setDocument(result.assets[0]);
        setImage(null);
        setResult(null);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const uploadDocument = async () => {
  if (!image && !document) {
    Alert.alert('No file selected', 'Please select an image or document first');
    return;
  }

  setLoading(true);
  setResult(null);

  // Animate progress bar
  Animated.timing(uploadProgress, {
    toValue: 1,
    duration: 2000,
    useNativeDriver: false,
  }).start();

  try {
    const formData = new FormData();
    
    if (image) {
      // Upload image
      formData.append('file', {
        uri: image,
        type: 'image/jpeg',
        name: 'document.jpg',
      } as any);
    } else if (document) {
      // Upload document - fix MIME type handling
      let mimeType = document.mimeType;
      
      // Fix for DOCX files (mobile sometimes sends wrong MIME type)
      if (document.name.toLowerCase().endsWith('.docx')) {
        mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      } else if (document.name.toLowerCase().endsWith('.pdf')) {
        mimeType = 'application/pdf';
      } else if (document.name.toLowerCase().endsWith('.doc')) {
        mimeType = 'application/msword';
      }
      
      formData.append('file', {
        uri: document.uri,
        type: mimeType,
        name: document.name,
      } as any);
    }

    console.log('📤 Uploading file:', document?.name || 'image');

    const response = await axios.post(`${API_URL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 90000, // 90 seconds for larger files
    });

    setResult(response.data);
    Alert.alert('Success! ✅', `Created: "${response.data.title}"`);
    uploadProgress.setValue(0);
  } catch (error: any) {
    console.error('Upload error:', error);
    uploadProgress.setValue(0);
    
    // Better error messages
    let errorMessage = 'An error occurred while uploading';
    
    if (error.response) {
      // Server responded with error
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data?.message;
      
      if (status === 400) {
        errorMessage = detail || 'Invalid file type. Please use JPG, PNG, PDF, or DOCX files.';
      } else if (status === 422) {
        errorMessage = detail || 'Could not extract text from the document. Please try a clearer image or different file.';
      } else if (status === 500) {
        errorMessage = detail || 'Server error. Please try again.';
      } else {
        errorMessage = detail || `Error ${status}: ${error.message}`;
      }
    } else if (error.request) {
      // Request made but no response
      errorMessage = 'Cannot connect to server. Check your network connection.';
    } else {
      errorMessage = error.message;
    }
    
    Alert.alert('Upload Failed', errorMessage);
  } finally {
    setLoading(false);
  }
};

  const clearSelection = () => {
    setImage(null);
    setDocument(null);
    setResult(null);
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.logoContainer}>
            <View style={styles.logoIcon}>
              <Ionicons name="document-text" size={24} color="#000" />
            </View>
            <Text style={styles.logoText}>Notion Hub</Text>
          </View>
          <Text style={styles.subtitle}>Transform documents into Notion pages</Text>
        </View>

        {/* Main Content Card */}
        <View style={styles.mainCard}>
          {!image && !document && !result && (
            <View style={styles.emptyState}>
              <View style={styles.emptyIconContainer}>
                <MaterialCommunityIcons name="file-upload-outline" size={64} color="#37352F40" />
              </View>
              <Text style={styles.emptyTitle}>Upload a document</Text>
              <Text style={styles.emptyDescription}>
                Choose an image, take a photo, or select a PDF or Word document to get started
              </Text>
            </View>
          )}

          {/* Image Preview */}
          {image && (
            <View style={styles.previewContainer}>
              <Image source={{ uri: image }} style={styles.imagePreview} />
              <TouchableOpacity style={styles.clearButton} onPress={clearSelection}>
                <Ionicons name="close-circle" size={24} color="#37352F" />
              </TouchableOpacity>
            </View>
          )}

          {/* Document Preview */}
          {document && (
            <View style={styles.documentPreview}>
              <View style={styles.documentIconContainer}>
                <MaterialCommunityIcons 
                  name={document.name.endsWith('.pdf') ? 'file-pdf-box' : 'file-word-box'} 
                  size={48} 
                  color="#37352F" 
                />
              </View>
              <View style={styles.documentInfo}>
                <Text style={styles.documentName} numberOfLines={2}>{document.name}</Text>
                <Text style={styles.documentMeta}>
                  {(document.size / 1024).toFixed(1)} KB
                </Text>
              </View>
              <TouchableOpacity onPress={clearSelection}>
                <Ionicons name="close-circle" size={24} color="#37352F60" />
              </TouchableOpacity>
            </View>
          )}

          {/* Success Result */}
          {result && (
            <View style={styles.successContainer}>
              <View style={styles.successIcon}>
                <Ionicons name="checkmark-circle" size={48} color="#0F7B6C" />
              </View>
              <Text style={styles.successTitle}>Page created successfully</Text>
              <View style={styles.resultCard}>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Title</Text>
                  <Text style={styles.resultValue}>{result.title}</Text>
                </View>
                <View style={styles.divider} />
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Page ID</Text>
                  <Text style={styles.resultValueMono}>{result.page_id.substring(0, 20)}...</Text>
                </View>
              </View>
              <TouchableOpacity style={styles.newUploadButton} onPress={clearSelection}>
                <Text style={styles.newUploadText}>Upload another document</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Action Buttons */}
        {!result && (
          <View style={styles.actionSection}>
            <Text style={styles.actionTitle}>Choose source</Text>
            
            <View style={styles.buttonGrid}>
              <TouchableOpacity 
                style={styles.actionButton} 
                onPress={takePhoto}
                activeOpacity={0.7}
              >
                <View style={styles.iconCircle}>
                  <Ionicons name="camera" size={24} color="#37352F" />
                </View>
                <Text style={styles.actionButtonText}>Camera</Text>
              </TouchableOpacity>

              <TouchableOpacity 
                style={styles.actionButton} 
                onPress={pickImage}
                activeOpacity={0.7}
              >
                <View style={styles.iconCircle}>
                  <Ionicons name="images" size={24} color="#37352F" />
                </View>
                <Text style={styles.actionButtonText}>Gallery</Text>
              </TouchableOpacity>

              <TouchableOpacity 
                style={styles.actionButton} 
                onPress={pickDocument}
                activeOpacity={0.7}
              >
                <View style={styles.iconCircle}>
                  <MaterialCommunityIcons name="file-document" size={24} color="#37352F" />
                </View>
                <Text style={styles.actionButtonText}>Document</Text>
              </TouchableOpacity>
            </View>

            {/* Upload Button */}
            {(image || document) && (
              <TouchableOpacity
                style={[styles.uploadButton, loading && styles.uploadButtonDisabled]}
                onPress={uploadDocument}
                disabled={loading}
                activeOpacity={0.8}
              >
                {loading ? (
                  <>
                    <ActivityIndicator color="#FFF" style={{ marginRight: 8 }} />
                    <Text style={styles.uploadButtonText}>Processing...</Text>
                  </>
                ) : (
                  <>
                    <Ionicons name="cloud-upload" size={20} color="#FFF" style={{ marginRight: 8 }} />
                    <Text style={styles.uploadButtonText}>Upload to Notion</Text>
                  </>
                )}
              </TouchableOpacity>
            )}

            {/* Loading Progress */}
            {loading && (
              <View style={styles.progressBarContainer}>
                <Animated.View 
                  style={[
                    styles.progressBar,
                    {
                      width: uploadProgress.interpolate({
                        inputRange: [0, 1],
                        outputRange: ['0%', '100%'],
                      }),
                    },
                  ]} 
                />
              </View>
            )}
          </View>
        )}

        {/* Footer Info */}
        <View style={styles.footer}>
          <View style={styles.infoCard}>
            <Ionicons name="information-circle-outline" size={16} color="#37352F60" />
            <Text style={styles.infoText}>
              Supports JPG, PNG, PDF, and DOCX files
            </Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  header: {
    paddingTop: 20,
    paddingBottom: 24,
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  logoIcon: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: '#F7F6F3',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  logoText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#37352F',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 15,
    color: '#37352F60',
    marginLeft: 48,
  },
  mainCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E9E9E7',
    padding: 24,
    marginBottom: 24,
    minHeight: 300,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  emptyIconContainer: {
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#37352F',
    marginBottom: 8,
  },
  emptyDescription: {
    fontSize: 14,
    color: '#37352F60',
    textAlign: 'center',
    lineHeight: 20,
    maxWidth: 280,
  },
  previewContainer: {
    position: 'relative',
    alignItems: 'center',
  },
  imagePreview: {
    width: '100%',
    height: 400,
    borderRadius: 8,
    backgroundColor: '#F7F6F3',
  },
  clearButton: {
    position: 'absolute',
    top: 12,
    right: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  documentPreview: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#F7F6F3',
    borderRadius: 8,
  },
  documentIconContainer: {
    marginRight: 16,
  },
  documentInfo: {
    flex: 1,
  },
  documentName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#37352F',
    marginBottom: 4,
  },
  documentMeta: {
    fontSize: 13,
    color: '#37352F60',
  },
  successContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  successIcon: {
    marginBottom: 16,
  },
  successTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#37352F',
    marginBottom: 20,
  },
  resultCard: {
    width: '100%',
    backgroundColor: '#F7F6F3',
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
  },
  resultRow: {
    marginVertical: 8,
  },
  resultLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#37352F60',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  resultValue: {
    fontSize: 15,
    color: '#37352F',
    fontWeight: '500',
  },
  resultValueMono: {
    fontSize: 13,
    color: '#37352F',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  divider: {
    height: 1,
    backgroundColor: '#E9E9E7',
    marginVertical: 8,
  },
  newUploadButton: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#E9E9E7',
  },
  newUploadText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#37352F',
  },
  actionSection: {
    marginBottom: 24,
  },
  actionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#37352F60',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 16,
  },
  buttonGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  actionButton: {
    flex: 1,
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E9E9E7',
    marginHorizontal: 4,
  },
  iconCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#F7F6F3',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  actionButtonText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#37352F',
  },
  uploadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#37352F',
    paddingVertical: 16,
    borderRadius: 8,
    marginTop: 8,
  },
  uploadButtonDisabled: {
    backgroundColor: '#37352F80',
  },
  uploadButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  progressBarContainer: {
    height: 3,
    backgroundColor: '#E9E9E7',
    borderRadius: 2,
    marginTop: 12,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#37352F',
    borderRadius: 2,
  },
  footer: {
    marginTop: 8,
  },
  infoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#F7F6F3',
    borderRadius: 8,
  },
  infoText: {
    fontSize: 13,
    color: '#37352F60',
    marginLeft: 8,
    flex: 1,
  },
});